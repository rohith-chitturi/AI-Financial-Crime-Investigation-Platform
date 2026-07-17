import os
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from typing import List, Dict, Any, Tuple

from app.ml.feature_engineering import FeatureEngineer

MODEL_PATH = os.path.join(os.path.dirname(__file__), "isolation_forest.joblib")
MODEL_VERSION = "1.0.0"

class AnomalyDetectionModel:
    def __init__(self):
        self.model = None
        self.min_score = -1.0
        self.max_score = 0.0
        self.is_loaded = False
        
    def load(self):
        if os.path.exists(MODEL_PATH):
            data = joblib.load(MODEL_PATH)
            self.model = data["model"]
            self.min_score = data.get("min_score", -1.0)
            self.max_score = data.get("max_score", 0.0)
            self.is_loaded = True
        else:
            # Fallback if no model is trained yet
            self.model = IsolationForest(contamination=0.05, random_state=42)
            self.is_loaded = False
            
    def train(self, features_matrix: List[List[float]]):
        """
        Trains the Isolation Forest on a batch of feature vectors and saves the model.
        """
        X = np.array(features_matrix)
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.model.fit(X)
        
        # Calculate score bounds for normalization
        scores = self.model.score_samples(X)
        self.min_score = float(np.min(scores))
        self.max_score = float(np.max(scores))
        
        # Save model
        joblib.dump({
            "model": self.model,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "version": MODEL_VERSION
        }, MODEL_PATH)
        self.is_loaded = True
        
    def _normalize_score(self, raw_score: float) -> float:
        """
        Converts the raw IsolationForest score (negative, where lower is more anomalous)
        to a 0-100 risk score (where 100 is maximum risk/anomaly).
        """
        # raw_score is typically between -1.0 and 0.0
        # Lower means more anomalous
        if self.max_score == self.min_score:
            return 50.0
            
        # Clip score to seen bounds
        score = max(self.min_score, min(self.max_score, raw_score))
        
        # Normalize to 0.0 - 1.0 (where 0 is normal, 1 is anomalous)
        # raw_score close to max_score -> normal -> 0
        # raw_score close to min_score -> anomaly -> 1
        normalized = (self.max_score - score) / (self.max_score - self.min_score)
        
        return normalized * 100.0
        
    def predict_risk(self, features: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Scores a single transaction and returns the 0-100 ML anomaly score 
        along with an explanation of contributing behavioral signals based on feature deviations.
        """
        if not self.is_loaded:
            self.load()
            if not self.is_loaded:
                # Mock a score if model isn't trained yet during development
                return 0.0, ["Model not trained yet"]
                
        feature_vector = FeatureEngineer.extract_feature_vector(features)
        X = np.array([feature_vector])
        
        raw_score = float(self.model.score_samples(X)[0])
        risk_score = self._normalize_score(raw_score)
        
        # Generate explanations based on simple feature thresholds/deviations
        explanations = []
        if features.get("amount_deviation_pct", 0) > 2.0:
            explanations.append(f"Transaction amount is significantly above historical average (+{features['amount_deviation_pct']:.0%}).")
        if features.get("tx_24h_count", 0) > 10:
            explanations.append(f"Unusually high transaction velocity ({int(features['tx_24h_count'])} transactions in 24h).")
        if features.get("time_since_prev_tx_seconds", 99999) < 60 and features.get("time_since_prev_tx_seconds", -1) != -1:
            explanations.append("Transaction occurred unusually close in time to the previous transaction.")
        if features.get("unique_beneficiaries_count", 0) > 5:
            explanations.append("High number of unique beneficiaries recently.")
            
        if not explanations and risk_score > 60:
            explanations.append("Multivariate anomaly detected by Isolation Forest.")
            
        return risk_score, explanations

# Singleton instance
ml_anomaly_detector = AnomalyDetectionModel()
