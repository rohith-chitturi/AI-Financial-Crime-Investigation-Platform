from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.db.models.transaction import Transaction
from app.db.models.account import Account

class AMLRuleEngine:
    
    @staticmethod
    async def evaluate_transaction(db: AsyncSession, transaction: Transaction, features: Dict[str, Any]) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Evaluates deterministic AML rules against a transaction.
        Returns a normalized rule score (0-100) and a list of triggered rule details.
        """
        triggered_rules = []
        total_risk_contribution = 0.0
        
        # 1. Structuring Detection
        # Rule: Amount is just below reporting threshold (e.g., $10,000) and multiple recent transactions
        if 9000 <= features.get("transaction_amount", 0) < 10000:
            if features.get("tx_24h_count", 0) >= 2:
                triggered_rules.append({
                    "rule_id": "AML-001",
                    "rule_name": "Structuring Detection",
                    "description": "Transaction amount is just below reporting threshold with multiple recent transactions.",
                    "severity": "HIGH",
                    "risk_contribution": 80.0
                })
                
        # 2. High Transaction Velocity
        # Rule: High number of transactions in a short period (e.g., > 10 in 24h)
        if features.get("tx_24h_count", 0) > 10:
             triggered_rules.append({
                "rule_id": "AML-002",
                "rule_name": "High Transaction Velocity",
                "description": f"Unusually high number of transactions ({int(features.get('tx_24h_count', 0))}) in 24 hours.",
                "severity": "MEDIUM",
                "risk_contribution": 50.0
            })
             
        # 3. Unusual High-Value Transaction / Sudden Deviation
        if features.get("amount_deviation_pct", 0) > 3.0: # > 300% deviation
            triggered_rules.append({
                "rule_id": "AML-003",
                "rule_name": "Unusual High-Value Transaction",
                "description": f"Transaction amount is {features.get('amount_deviation_pct')*100:.0f}% higher than historical average.",
                "severity": "HIGH",
                "risk_contribution": 70.0
            })
            
        # 4. Dormant Account Activation
        # Rule: No transactions in last 90 days, but account is old
        age = features.get("account_age_days", 0)
        time_since_prev = features.get("time_since_prev_tx_seconds", -1)
        if age > 90 and (time_since_prev == -1 or time_since_prev > 90 * 86400):
            triggered_rules.append({
                "rule_id": "AML-004",
                "rule_name": "Dormant Account Activation",
                "description": "Activity on an account that has been dormant for over 90 days.",
                "severity": "MEDIUM",
                "risk_contribution": 60.0
            })
            
        # 5. Rapid Movement of Funds
        # Rule: Funds received and immediately transferred out (can check in_out_ratio and time_since_prev)
        if features.get("time_since_prev_tx_seconds", 99999) < 300 and features.get("time_since_prev_tx_seconds", -1) != -1:
            triggered_rules.append({
                "rule_id": "AML-005",
                "rule_name": "Rapid Movement of Funds",
                "description": "Transactions occurred within 5 minutes of each other.",
                "severity": "MEDIUM",
                "risk_contribution": 40.0
            })

        # Calculate final rule score (Max capping at 100)
        for rule in triggered_rules:
            total_risk_contribution += rule["risk_contribution"]
            
        rule_score = min(100.0, total_risk_contribution)
        
        return rule_score, triggered_rules
