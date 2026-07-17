import asyncio
import os
import sys
import numpy as np

# Add the backend directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import AsyncSessionLocal
from app.db.models.transaction import Transaction
from app.services.risk_scoring import RiskScoringService
from app.ml.anomaly_detection import ml_anomaly_detector
from app.ml.feature_engineering import FeatureEngineer
from app.core.config import settings

async def evaluate():
    print("Starting Model Evaluation...")
    
    async with AsyncSessionLocal() as db:
        # 1. Fetch normal transactions to train Isolation Forest
        print("Fetching normal transactions for ML training...")
        normal_tx_query = await db.execute(
            select(Transaction).where(Transaction.is_suspicious_ground_truth == False).limit(500)
        )
        normal_txs = normal_tx_query.scalars().all()
        
        print(f"Found {len(normal_txs)} normal transactions. Extracting features...")
        training_features = []
        for tx in normal_txs:
            feats = await FeatureEngineer.compute_features_for_transaction(db, tx)
            vec = FeatureEngineer.extract_feature_vector(feats)
            training_features.append(vec)
            
        print("Training Isolation Forest...")
        ml_anomaly_detector.train(training_features)
        print("Model trained and saved successfully.")
        
        # 2. Fetch evaluation set (Mix of normal and suspicious)
        print("Fetching test set...")
        test_tx_query = await db.execute(select(Transaction).limit(1000))
        test_txs = test_tx_query.scalars().all()
        
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0
        
        print(f"Scoring {len(test_txs)} transactions...")
        for tx in test_txs:
            # We bypass the API and call the service directly
            analysis = await RiskScoringService.analyze_transaction(db, str(tx.id))
            
            is_alert = analysis.unified_risk_score >= settings.ALERT_THRESHOLD
            is_ground_truth = tx.is_suspicious_ground_truth
            
            if is_alert and is_ground_truth:
                true_positives += 1
            elif is_alert and not is_ground_truth:
                false_positives += 1
            elif not is_alert and not is_ground_truth:
                true_negatives += 1
            elif not is_alert and is_ground_truth:
                false_negatives += 1
                
        # 3. Calculate metrics
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        print("\n--- Evaluation Results ---")
        print(f"Total Evaluated: {len(test_txs)}")
        print(f"True Positives: {true_positives}")
        print(f"False Positives: {false_positives}")
        print(f"True Negatives: {true_negatives}")
        print(f"False Negatives: {false_negatives}")
        print(f"\nPrecision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1 Score:  {f1_score:.4f}")

if __name__ == "__main__":
    asyncio.run(evaluate())
