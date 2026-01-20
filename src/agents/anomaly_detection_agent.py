"""
Anomaly Detection Agent
Detects unusual transactions using statistical methods and pattern analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class AnomalyDetectionAgent:
    """Detects anomalies in financial transactions using multiple detection methods."""
    
    def __init__(self, z_score_threshold: float = 2.5, iqr_multiplier: float = 1.5):
        """
        Initialize anomaly detection agent.
        
        Args:
            z_score_threshold: Z-score threshold for statistical outlier detection (default: 2.5)
            iqr_multiplier: IQR multiplier for outlier detection (default: 1.5)
        """
        self.z_score_threshold = z_score_threshold
        self.iqr_multiplier = iqr_multiplier
    
    def detect_anomalies(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect anomalies in transactions dataframe.
        
        Args:
            transactions_df: DataFrame with transaction data including 'amount', 'merchant', 'category', 'date'
            
        Returns:
            DataFrame with added 'is_anomaly' and 'anomaly_reason' columns
        """
        df = transactions_df.copy()
        
        # Ensure amount is numeric
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Initialize anomaly columns
        df['is_anomaly'] = False
        df['anomaly_reason'] = ''
        df['anomaly_score'] = 0.0
        
        # Apply multiple detection methods
        self._detect_statistical_outliers(df)
        self._detect_category_outliers(df)
        self._detect_unknown_merchants(df)
        self._detect_unusual_patterns(df)
        
        return df
    
    def _detect_statistical_outliers(self, df: pd.DataFrame):
        """Detect outliers using Z-score and IQR methods."""
        if len(df) < 3:  # Need at least 3 transactions for statistical analysis
            return
        
        amounts = df['amount'].dropna()
        if len(amounts) < 3:
            return
        
        # Z-score method
        mean_amount = amounts.mean()
        std_amount = amounts.std()
        
        if std_amount > 0:
            z_scores = np.abs((df['amount'] - mean_amount) / std_amount)
            z_outliers = z_scores > self.z_score_threshold
            
            for idx in df[z_outliers].index:
                if not df.at[idx, 'is_anomaly']:
                    df.at[idx, 'is_anomaly'] = True
                    df.at[idx, 'anomaly_reason'] = (
                        f"Statistical outlier: Z-score {z_scores[idx]:.2f} "
                        f"(amount ${df.at[idx, 'amount']:.2f} vs mean ${mean_amount:.2f})"
                    )
                    df.at[idx, 'anomaly_score'] = max(df.at[idx, 'anomaly_score'], z_scores[idx])
        
        # IQR method
        Q1 = amounts.quantile(0.25)
        Q3 = amounts.quantile(0.75)
        IQR = Q3 - Q1
        
        if IQR > 0:
            lower_bound = Q1 - self.iqr_multiplier * IQR
            upper_bound = Q3 + self.iqr_multiplier * IQR
            
            iqr_outliers = (df['amount'] < lower_bound) | (df['amount'] > upper_bound)
            
            for idx in df[iqr_outliers].index:
                if not df.at[idx, 'is_anomaly']:
                    df.at[idx, 'is_anomaly'] = True
                    reason = (
                        f"IQR outlier: Amount ${df.at[idx, 'amount']:.2f} "
                        f"outside range [${lower_bound:.2f}, ${upper_bound:.2f}]"
                    )
                    if df.at[idx, 'anomaly_reason']:
                        df.at[idx, 'anomaly_reason'] += f"; {reason}"
                    else:
                        df.at[idx, 'anomaly_reason'] = reason
                    # Calculate score based on how far outside the bounds
                    if df.at[idx, 'amount'] > upper_bound:
                        score = (df.at[idx, 'amount'] - upper_bound) / IQR
                    else:
                        score = (lower_bound - df.at[idx, 'amount']) / IQR
                    df.at[idx, 'anomaly_score'] = max(df.at[idx, 'anomaly_score'], score)
    
    def _detect_category_outliers(self, df: pd.DataFrame):
        """Detect outliers within specific categories."""
        if 'category' not in df.columns:
            return
        
        for category in df['category'].unique():
            category_df = df[df['category'] == category]
            if len(category_df) < 2:  # Need at least 2 transactions in category
                continue
            
            category_amounts = category_df['amount'].dropna()
            if len(category_amounts) < 2:
                continue
            
            category_mean = category_amounts.mean()
            category_std = category_amounts.std()
            
            if category_std > 0:
                # Detect transactions significantly above category average
                threshold = category_mean + 2 * category_std
                outliers = (category_df['amount'] > threshold) & category_df.index.isin(df.index)
                
                for idx in category_df[category_df['amount'] > threshold].index:
                    if not df.at[idx, 'is_anomaly']:
                        df.at[idx, 'is_anomaly'] = True
                        reason = (
                            f"Category outlier: ${df.at[idx, 'amount']:.2f} in '{category}' "
                            f"(category avg: ${category_mean:.2f})"
                        )
                        if df.at[idx, 'anomaly_reason']:
                            df.at[idx, 'anomaly_reason'] += f"; {reason}"
                        else:
                            df.at[idx, 'anomaly_reason'] = reason
                        df.at[idx, 'anomaly_score'] = max(
                            df.at[idx, 'anomaly_score'],
                            (df.at[idx, 'amount'] - category_mean) / category_std
                        )
    
    def _detect_unknown_merchants(self, df: pd.DataFrame):
        """Detect transactions from unknown or suspicious merchants."""
        if 'merchant' not in df.columns:
            return
        
        # Flag generic/unknown merchant names
        suspicious_keywords = [
            'unknown', 'payment', 'card transaction', 'square', 
            'transfer', 'pending', 'unidentified'
        ]
        
        merchant_lower = df['merchant'].astype(str).str.lower()
        
        for idx, merchant in merchant_lower.items():
            if any(keyword in merchant for keyword in suspicious_keywords):
                if not df.at[idx, 'is_anomaly']:
                    df.at[idx, 'is_anomaly'] = True
                    reason = f"Unknown/suspicious merchant: '{df.at[idx, 'merchant']}'"
                    if df.at[idx, 'anomaly_reason']:
                        df.at[idx, 'anomaly_reason'] += f"; {reason}"
                    else:
                        df.at[idx, 'anomaly_reason'] = reason
                    df.at[idx, 'anomaly_score'] = max(df.at[idx, 'anomaly_score'], 1.0)
    
    def _detect_unusual_patterns(self, df: pd.DataFrame):
        """Detect unusual spending patterns."""
        if 'date' not in df.columns or len(df) < 3:
            return
        
        # Detect unusually large single transactions
        amounts = df['amount'].dropna()
        if len(amounts) > 0:
            median_amount = amounts.median()
            # Flag transactions more than 5x the median
            large_transaction_threshold = median_amount * 5
            
            large_transactions = df['amount'] > large_transaction_threshold
            for idx in df[large_transactions].index:
                if not df.at[idx, 'is_anomaly']:
                    df.at[idx, 'is_anomaly'] = True
                    reason = (
                        f"Unusually large transaction: ${df.at[idx, 'amount']:.2f} "
                        f"(>{large_transaction_threshold:.2f}, median: ${median_amount:.2f})"
                    )
                    if df.at[idx, 'anomaly_reason']:
                        df.at[idx, 'anomaly_reason'] += f"; {reason}"
                    else:
                        df.at[idx, 'anomaly_reason'] = reason
                    df.at[idx, 'anomaly_score'] = max(
                        df.at[idx, 'anomaly_score'],
                        df.at[idx, 'amount'] / median_amount
                    )
    
    def get_anomaly_summary(self, df: pd.DataFrame) -> Dict:
        """Generate summary of detected anomalies."""
        anomalies = df[df['is_anomaly'] == True]
        
        summary = {
            'total_anomalies': len(anomalies),
            'anomaly_rate': len(anomalies) / len(df) * 100 if len(df) > 0 else 0,
            'anomalies_by_type': {},
            'top_anomalies': []
        }
        
        if len(anomalies) > 0:
            # Categorize by reason type
            for reason in anomalies['anomaly_reason']:
                if 'Statistical outlier' in reason or 'Z-score' in reason:
                    summary['anomalies_by_type']['Statistical Outlier'] = \
                        summary['anomalies_by_type'].get('Statistical Outlier', 0) + 1
                elif 'IQR outlier' in reason:
                    summary['anomalies_by_type']['IQR Outlier'] = \
                        summary['anomalies_by_type'].get('IQR Outlier', 0) + 1
                elif 'Category outlier' in reason:
                    summary['anomalies_by_type']['Category Outlier'] = \
                        summary['anomalies_by_type'].get('Category Outlier', 0) + 1
                elif 'Unknown/suspicious merchant' in reason:
                    summary['anomalies_by_type']['Unknown Merchant'] = \
                        summary['anomalies_by_type'].get('Unknown Merchant', 0) + 1
                elif 'Unusually large' in reason:
                    summary['anomalies_by_type']['Large Transaction'] = \
                        summary['anomalies_by_type'].get('Large Transaction', 0) + 1
            
            # Get top anomalies by score
            top_anomalies = anomalies.nlargest(5, 'anomaly_score')
            summary['top_anomalies'] = top_anomalies[
                ['date', 'merchant', 'amount', 'category', 'anomaly_reason', 'anomaly_score']
            ].to_dict('records')
        
        return summary
    
    def generate_anomaly_report(self, df: pd.DataFrame) -> str:
        """Generate formatted text report of anomalies."""
        anomalies = df[df['is_anomaly'] == True]
        summary = self.get_anomaly_summary(df)
        
        report_lines = [
            "=" * 60,
            "ANOMALY DETECTION REPORT",
            "=" * 60,
            "",
            f"Total Transactions Analyzed: {len(df)}",
            f"Anomalies Detected: {summary['total_anomalies']}",
            f"Anomaly Rate: {summary['anomaly_rate']:.1f}%",
            "",
        ]
        
        if summary['anomalies_by_type']:
            report_lines.extend([
                "ANOMALIES BY TYPE:",
                "-" * 60,
            ])
            for anomaly_type, count in summary['anomalies_by_type'].items():
                report_lines.append(f"  {anomaly_type:30s} {count:>3d}")
            report_lines.append("")
        
        if summary['top_anomalies']:
            report_lines.extend([
                "TOP ANOMALIES (by severity):",
                "-" * 60,
            ])
            for i, anomaly in enumerate(summary['top_anomalies'], 1):
                report_lines.extend([
                    f"\n{i}. {anomaly.get('merchant', 'N/A')} - ${anomaly.get('amount', 0):,.2f}",
                    f"   Date: {anomaly.get('date', 'N/A')}",
                    f"   Category: {anomaly.get('category', 'N/A')}",
                    f"   Score: {anomaly.get('anomaly_score', 0):.2f}",
                    f"   Reason: {anomaly.get('anomaly_reason', 'N/A')}",
                ])
        
        if len(anomalies) == 0:
            report_lines.append("No anomalies detected. All transactions appear normal.")
        
        report_lines.extend([
            "",
            "=" * 60,
        ])
        
        return "\n".join(report_lines)
