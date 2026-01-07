from dataclasses import dataclass
from datetime import date
from typing import Optional


# Define a dataclass to represent a financial transaction
#Allows for optional description and category with confidence level and lessen randomness

@dataclass
class Transaction:
    transaction_id: str
    date: date
    merchant: str
    amount: float
    description: Optional[str]
    category: Optional[str] = None
    category_confidence: Optional[float] = None
