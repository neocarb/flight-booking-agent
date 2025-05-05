from typing import List, Optional
from datetime import date
from dataclasses import dataclass

@dataclass
class PassengerDTO:
    phone_number: str
    email: str
    born_on: str
    title: str
    gender: str
    family_name: str
    given_name: str
    id: str
