from dataclasses import dataclass

@dataclass
class OfferDTO:
    offerId: str
    totalCost: float
    origin: str
    destination: str = ""
    airlineName: str = ""
    departureTime: str = ""
    arrivalTime: str = ""
    duration: str = ""