import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid

from app.db.models.transaction import Transaction
from app.db.models.account import Account
from app.db.models.customer import Customer

class FeatureEngineer:
    
    @staticmethod
    async def compute_features_for_transaction(db: AsyncSession, transaction: Transaction) -> Dict[str, Any]:
        """
        Computes behavioral features for a transaction strictly using data available 
        at or before the transaction timestamp to prevent future-data leakage.
        """
        # Determine the primary account for feature extraction
        account_id = transaction.source_account_id if transaction.source_account_id else transaction.destination_account_id
        
        if not account_id:
            # Fallback if no account is linked (e.g., cash deposit without account, rare)
            return FeatureEngineer._get_default_features(transaction)

        # 1. Fetch Account and Customer
        account_query = await db.execute(
            select(Account, Customer)
            .join(Customer, Account.customer_id == Customer.id)
            .where(Account.id == account_id)
        )
        result = account_query.first()
        if not result:
            return FeatureEngineer._get_default_features(transaction)
            
        account, customer = result
        
        tx_time = transaction.timestamp
        tx_amount = float(transaction.amount)
        
        # 2. Historical Queries up to tx_time
        # We need:
        # - Previous transaction timestamp
        # - Count of transactions in 1h, 24h, 7d
        # - Average historical amount
        # - Count of unique beneficiaries
        # - Incoming / Outgoing ratio
        
        historical_tx_query = await db.execute(
            select(
                Transaction.timestamp,
                Transaction.amount,
                Transaction.destination_account_id,
                Transaction.source_account_id
            ).where(
                or_(
                    Transaction.source_account_id == account_id,
                    Transaction.destination_account_id == account_id
                ),
                Transaction.timestamp < tx_time
            ).order_by(Transaction.timestamp.desc())
        )
        
        history = historical_tx_query.all()
        
        # 3. Calculate features manually from history to avoid complex multiple SQL aggregations
        # This is fast enough for single-transaction API analysis
        
        time_since_prev_tx = -1.0 # default if no history
        if history:
            prev_time = history[0].timestamp
            time_since_prev_tx = (tx_time - prev_time).total_seconds()
            
        tx_1h_count = 0
        tx_24h_count = 0
        tx_7d_count = 0
        
        total_hist_amount = 0.0
        unique_beneficiaries = set()
        incoming_count = 0
        outgoing_count = 0
        
        time_1h_ago = tx_time - timedelta(hours=1)
        time_24h_ago = tx_time - timedelta(hours=24)
        time_7d_ago = tx_time - timedelta(days=7)
        
        for h_tx in history:
            h_time, h_amount, h_dest, h_src = h_tx
            
            # Frequency
            if h_time >= time_1h_ago:
                tx_1h_count += 1
            if h_time >= time_24h_ago:
                tx_24h_count += 1
            if h_time >= time_7d_ago:
                tx_7d_count += 1
                
            # Averages
            total_hist_amount += float(h_amount)
            
            # Ratio
            if h_src == account_id:
                outgoing_count += 1
                if h_dest:
                    unique_beneficiaries.add(h_dest)
            elif h_dest == account_id:
                incoming_count += 1
                
        hist_count = len(history)
        avg_hist_amount = (total_hist_amount / hist_count) if hist_count > 0 else tx_amount
        
        # Deviation
        deviation = 0.0
        if avg_hist_amount > 0:
            deviation = (tx_amount - avg_hist_amount) / avg_hist_amount
            
        # Incoming/Outgoing Ratio
        in_out_ratio = float(incoming_count) / float(outgoing_count) if outgoing_count > 0 else float(incoming_count)
        
        # Velocity (Total amount in last 24h)
        # We can sum it up or just use count. Let's use count for velocity here, or amount/day. 
        # We'll use 24h count as velocity feature
        
        # Account Age
        account_age_days = (tx_time - account.created_at).days
        
        features = {
            "transaction_amount": tx_amount,
            "time_since_prev_tx_seconds": time_since_prev_tx,
            "tx_1h_count": float(tx_1h_count),
            "tx_24h_count": float(tx_24h_count),
            "tx_7d_count": float(tx_7d_count),
            "historical_avg_amount": avg_hist_amount,
            "amount_deviation_pct": deviation,
            "unique_beneficiaries_count": float(len(unique_beneficiaries)),
            "in_out_ratio": in_out_ratio,
            "account_age_days": float(account_age_days),
            "customer_base_risk": customer.risk_score,
            "transaction_hour": float(tx_time.hour),
            "transaction_day_of_week": float(tx_time.weekday())
        }
        
        return features

    @staticmethod
    def _get_default_features(transaction: Transaction) -> Dict[str, Any]:
        """Fallback features if account doesn't exist."""
        return {
            "transaction_amount": float(transaction.amount),
            "time_since_prev_tx_seconds": -1.0,
            "tx_1h_count": 0.0,
            "tx_24h_count": 0.0,
            "tx_7d_count": 0.0,
            "historical_avg_amount": float(transaction.amount),
            "amount_deviation_pct": 0.0,
            "unique_beneficiaries_count": 0.0,
            "in_out_ratio": 0.0,
            "account_age_days": 0.0,
            "customer_base_risk": 0.5,
            "transaction_hour": float(transaction.timestamp.hour),
            "transaction_day_of_week": float(transaction.timestamp.weekday())
        }
    
    @staticmethod
    def extract_feature_vector(features: Dict[str, Any]) -> List[float]:
        """
        Converts the feature dictionary to a list of floats in a fixed order for ML inference.
        """
        ordered_keys = [
            "transaction_amount",
            "time_since_prev_tx_seconds",
            "tx_1h_count",
            "tx_24h_count",
            "tx_7d_count",
            "historical_avg_amount",
            "amount_deviation_pct",
            "unique_beneficiaries_count",
            "in_out_ratio",
            "account_age_days",
            "customer_base_risk",
            "transaction_hour",
            "transaction_day_of_week"
        ]
        return [float(features[k]) for k in ordered_keys]
