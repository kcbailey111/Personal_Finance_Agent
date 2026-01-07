import pandas as pd
from datetime import datetime
from uuid import uuid4
from typing import List

from utils.schema import Transaction

#Input path is passed when initializing the agent
#Input is validated and cleaned before creating Transaction objects

class IngestionAgent:
    def __init__(self, input_path: str):
        self.input_path = input_path

    def load_transactions(self) -> List[Transaction]:
        df = pd.read_csv(self.input_path)

        transactions = []
        for _, row in df.iterrows():
            txn = Transaction(
                transaction_id=str(uuid4()),
                date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                merchant=row["merchant"].strip(),
                amount=float(row["amount"]),
                description=row.get("description", None),
            )
            transactions.append(txn)

        return transactions

