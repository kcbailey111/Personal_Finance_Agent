import pandas as pd
from pathlib import Path
from typing import List, Dict, Any


class IngestionAgent:
    def __init__(self, input_path: Path):
        self.input_path = input_path

    def load_transactions(self) -> List[Dict[str, Any]]:
        df = pd.read_csv(self.input_path)

        # CRITICAL LINE
        # Converts each row into a dictionary
        transactions = df.to_dict(orient="records")

        return transactions

