from typing import List, Optional
from datetime import date
from dataclasses import dataclass

@dataclass
class PaymentDTO:
    currency: str
    amount: float
