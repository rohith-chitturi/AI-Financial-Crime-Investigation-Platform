import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Any

from app.db.models.transaction import Transaction
from app.db.models.account import Account
from app.db.models.alert import Alert
from app.db.models.risk_analysis import TransactionRiskAnalysis
from app.ml.feature_engineering import FeatureEngineer
from app.ml.anomaly_detection import ml_anomaly_detector, MODEL_VERSION
from app.services.aml_rules import AMLRuleEngine
from app.core.config import settings

class RiskScoringService:
    
    @staticmethod
    async def analyze_transaction(db: AsyncSession, neo4j_session: Any, transaction_id: str, background_tasks=None) -> TransactionRiskAnalysis:
        start_time = time.time()
        
        # 1. Fetch Transaction
        result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
            
        # 2. Extract Features
        features = await FeatureEngineer.compute_features_for_transaction(db, transaction)
        
        # 3. Machine Learning Anomaly Detection
        ml_score, ml_explanations = ml_anomaly_detector.predict_risk(features)
        
        # 4. AML Rule Engine
        aml_score, triggered_rules = await AMLRuleEngine.evaluate_transaction(db, transaction, features)
        
        # 5. Knowledge Graph Risk Analysis
        from app.services.graph_analysis import GraphAnalysisService
        graph_risk_data = await GraphAnalysisService.analyze_transaction_risk(
            neo4j_session, 
            str(transaction.source_account_id), 
            str(transaction.destination_account_id) if transaction.destination_account_id else None
        )
        graph_score = graph_risk_data["graph_score"]
        graph_evidence = graph_risk_data["graph_evidence"]
        graph_version = graph_risk_data["graph_version"]
        
        # 6. Customer Risk
        customer_score = features.get("customer_base_risk", 0.5) * 100.0
        
        # 7. Unified Risk Scoring
        unified_score = (
            (ml_score * settings.RISK_WEIGHT_ML) +
            (aml_score * settings.RISK_WEIGHT_AML_RULES) +
            (graph_score * settings.RISK_WEIGHT_GRAPH) +
            (customer_score * settings.RISK_WEIGHT_CUSTOMER)
        )
        
        # Determine Risk Level
        if unified_score >= settings.ALERT_THRESHOLD:
            risk_level = "Critical" if unified_score >= 90 else "High"
        elif unified_score >= 50:
            risk_level = "High"
        elif unified_score >= 25:
            risk_level = "Medium"
        else:
            risk_level = "Low"
            
        # 8. Generate Explainability
        explanation = RiskScoringService._generate_explanation(
            ml_score, ml_explanations,
            aml_score, triggered_rules,
            graph_score, graph_evidence,
            customer_score
        )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # 9. Persist Risk Analysis
        # Check if analysis already exists (idempotency)
        existing_analysis_query = await db.execute(
            select(TransactionRiskAnalysis).where(TransactionRiskAnalysis.transaction_id == transaction_id)
        )
        existing_analysis = existing_analysis_query.scalar_one_or_none()
        
        if existing_analysis:
            # Update existing if we rerun analysis
            analysis = existing_analysis
            analysis.ml_score = ml_score
            analysis.aml_rule_score = aml_score
            analysis.graph_score = graph_score
            analysis.customer_risk_score = customer_score
            analysis.unified_risk_score = unified_score
            analysis.risk_level = risk_level
            analysis.triggered_rules = triggered_rules
            analysis.graph_evidence = graph_evidence
            analysis.graph_version = graph_version
            analysis.explanation = explanation
            analysis.model_version = MODEL_VERSION
            analysis.processing_time_ms = processing_time_ms
        else:
            analysis = TransactionRiskAnalysis(
                transaction_id=transaction.id,
                model_version=MODEL_VERSION,
                ml_score=ml_score,
                aml_rule_score=aml_score,
                graph_score=graph_score,
                customer_risk_score=customer_score,
                unified_risk_score=unified_score,
                risk_level=risk_level,
                triggered_rules=triggered_rules,
                graph_evidence=graph_evidence,
                graph_version=graph_version,
                explanation=explanation,
                processing_time_ms=processing_time_ms
            )
            db.add(analysis)
            
        await db.commit()
        await db.refresh(analysis)
        
        # 10. Create Alert and Auto-Investigation if threshold met
        if unified_score >= settings.ALERT_THRESHOLD:
            await RiskScoringService._create_or_update_alert(db, transaction, analysis)
            if background_tasks:
                from app.api.v1.endpoints.investigations import run_investigation_task
                background_tasks.add_task(run_investigation_task, transaction.id, "AUTO")
            
        return analysis

    @staticmethod
    def _generate_explanation(ml_score: float, ml_explanations: list,
                              aml_score: float, triggered_rules: list,
                              graph_score: float, graph_evidence: list,
                              customer_score: float) -> str:
        parts = []
        
        if ml_explanations:
            parts.append(f"**Machine Learning Signals (Score: {ml_score:.1f}/100):**")
            for exp in ml_explanations:
                parts.append(f"- {exp}")
                
        if triggered_rules:
            parts.append(f"\n**Deterministic AML Rules (Score: {aml_score:.1f}/100):**")
            for rule in triggered_rules:
                parts.append(f"- [{rule['rule_id']}] {rule['rule_name']}: {rule['description']}")
                
        if graph_evidence:
            parts.append(f"\n**Knowledge Graph Network (Score: {graph_score:.1f}/100):**")
            for ev in graph_evidence:
                parts.append(f"- {ev}")
                
        if customer_score > 50:
            parts.append(f"\n**Customer Risk Factors (Score: {customer_score:.1f}/100):**")
            parts.append("- Customer has an elevated base risk profile.")
            
        if not parts:
            return "Transaction conforms to expected baseline behavior. No significant risk signals detected."
            
        return "\n".join(parts)

    @staticmethod
    async def _create_or_update_alert(db: AsyncSession, transaction: Transaction, analysis: TransactionRiskAnalysis):
        # Check for existing alert
        existing_alert_query = await db.execute(
            select(Alert).where(Alert.transaction_id == transaction.id)
        )
        existing_alert = existing_alert_query.scalar_one_or_none()
        
        # Need to know the customer_id associated with the alert for RBAC/routing
        # Assuming the source account's customer is the primary entity
        account_query = await db.execute(select(Account).where(Account.id == transaction.source_account_id))
        account = account_query.scalar_one_or_none()
        customer_id = account.customer_id if account else None
        
        # If no customer is found on source, try destination
        if not customer_id and transaction.destination_account_id:
             dest_account_query = await db.execute(select(Account).where(Account.id == transaction.destination_account_id))
             dest_account = dest_account_query.scalar_one_or_none()
             customer_id = dest_account.customer_id if dest_account else None
             
        if not customer_id:
             # If completely unassociated, we might not alert a specific customer, but for schema compliance we need one.
             # We can't really proceed if nullable=False, so let's fetch a dummy or fail.
             # The DB schema says customer_id nullable=False.
             raise ValueError("Cannot create alert: Transaction has no associated customer.")

        if existing_alert:
            existing_alert.unified_risk_score = analysis.unified_risk_score
            existing_alert.risk_level = analysis.risk_level
            existing_alert.triggered_aml_rules = analysis.triggered_rules
            existing_alert.model_version = analysis.model_version
        else:
            alert = Alert(
                transaction_id=transaction.id,
                customer_id=customer_id,
                unified_risk_score=analysis.unified_risk_score,
                risk_level=analysis.risk_level,
                triggered_aml_rules=analysis.triggered_rules,
                model_version=analysis.model_version,
                status="NEW"
            )
            db.add(alert)
            
        await db.commit()
