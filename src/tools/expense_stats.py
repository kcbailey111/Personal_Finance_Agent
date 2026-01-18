"""
Spending Analytics and Statistics Module
Generates comprehensive spending insights from categorized transactions.
"""

import pandas as pd
from typing import Dict, List
from pathlib import Path


class ExpenseAnalytics:
    """Generate spending analytics and insights from categorized transactions."""
    
    def __init__(self, transactions_df: pd.DataFrame):
        """
        Initialize analytics with transaction dataframe.
        
        Args:
            transactions_df: DataFrame with columns including 'amount', 'category', 'date'
        """
        self.df = transactions_df.copy()
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare data for analysis."""
        # Ensure amount is numeric
        self.df['amount'] = pd.to_numeric(self.df['amount'], errors='coerce')
        
        # Parse date if it's a string
        if 'date' in self.df.columns:
            self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce')
            self.df['month'] = self.df['date'].dt.to_period('M')
            self.df['year_month'] = self.df['date'].dt.strftime('%Y-%m')
    
    def get_category_summary(self) -> pd.DataFrame:
        """Get spending summary by category."""
        category_summary = (
            self.df.groupby('category', as_index=False)
            .agg({
                'amount': ['sum', 'count', 'mean']
            })
            .round(2)
        )
        
        category_summary.columns = ['category', 'total_spent', 'transaction_count', 'avg_transaction']
        category_summary = category_summary.sort_values('total_spent', ascending=False)
        
        # Calculate percentage of total
        total_all = category_summary['total_spent'].sum()
        category_summary['percentage'] = (category_summary['total_spent'] / total_all * 100).round(1)
        
        return category_summary
    
    def get_monthly_summary(self) -> pd.DataFrame:
        """Get monthly spending totals."""
        if 'year_month' not in self.df.columns:
            return pd.DataFrame()
        
        monthly = (
            self.df.groupby('year_month', as_index=False)
            .agg({
                'amount': ['sum', 'count']
            })
            .round(2)
        )
        
        monthly.columns = ['month', 'total_spent', 'transaction_count']
        monthly = monthly.sort_values('month')
        
        return monthly
    
    def get_category_by_month(self) -> pd.DataFrame:
        """Get spending by category and month."""
        if 'year_month' not in self.df.columns or 'category' not in self.df.columns:
            return pd.DataFrame()
        
        category_month = (
            self.df.groupby(['category', 'year_month'], as_index=False)
            .agg({'amount': 'sum'})
            .round(2)
        )
        category_month.columns = ['category', 'month', 'total_spent']
        
        return category_month
    
    def get_top_categories(self, n: int = 5) -> pd.DataFrame:
        """Get top N spending categories."""
        summary = self.get_category_summary()
        return summary.head(n)
    
    def get_top_merchants(self, n: int = 5) -> pd.DataFrame:
        """Get top N merchants by spending."""
        if 'merchant' not in self.df.columns:
            return pd.DataFrame()
        
        merchant_summary = (
            self.df.groupby('merchant', as_index=False)
            .agg({'amount': 'sum'})
            .sort_values('amount', ascending=False)
            .head(n)
            .round(2)
        )
        merchant_summary.columns = ['merchant', 'total_spent']
        
        return merchant_summary
    
    def get_total_spending(self) -> float:
        """Get total spending across all transactions."""
        return float(self.df['amount'].sum().round(2))
    
    def get_transaction_count(self) -> int:
        """Get total number of transactions."""
        return len(self.df)
    
    def generate_summary_report(self) -> str:
        """Generate a formatted text summary report."""
        total_spent = self.get_total_spending()
        transaction_count = self.get_transaction_count()
        top_categories = self.get_top_categories()
        monthly_summary = self.get_monthly_summary()
        
        report_lines = [
            "=" * 60,
            "SPENDING ANALYTICS DASHBOARD",
            "=" * 60,
            "",
            f"Total Spending: ${total_spent:,.2f}",
            f"Total Transactions: {transaction_count}",
            f"Average Transaction: ${(total_spent / transaction_count):,.2f}" if transaction_count > 0 else "",
            "",
            "TOP SPENDING CATEGORIES:",
            "-" * 60,
        ]
        
        # Add category breakdown
        for _, row in top_categories.iterrows():
            report_lines.append(
                f"  {row['category']:20s} ${row['total_spent']:>10,.2f}  "
                f"({row['percentage']:>5.1f}%)  [{int(row['transaction_count'])} transactions]"
            )
        
        # Add monthly summary if available
        if not monthly_summary.empty:
            report_lines.extend([
                "",
                "MONTHLY SPENDING SUMMARY:",
                "-" * 60,
            ])
            for _, row in monthly_summary.iterrows():
                report_lines.append(
                    f"  {row['month']:10s} ${row['total_spent']:>10,.2f}  "
                    f"[{int(row['transaction_count'])} transactions]"
                )
        
        # Add top merchants if available
        top_merchants = self.get_top_merchants()
        if not top_merchants.empty:
            report_lines.extend([
                "",
                "TOP MERCHANTS BY SPENDING:",
                "-" * 60,
            ])
            for _, row in top_merchants.iterrows():
                report_lines.append(
                    f"  {row['merchant']:30s} ${row['total_spent']:>10,.2f}"
                )
        
        report_lines.extend([
            "",
            "=" * 60,
        ])
        
        return "\n".join(report_lines)
    
    def save_summary_to_file(self, output_path: Path):
        """Save summary report to a text file."""
        report = self.generate_summary_report()
        output_path.write_text(report, encoding='utf-8')
