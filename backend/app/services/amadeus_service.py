from amadeus import Client, ResponseError
from app.core.config import AMADEUS_API_KEY, AMADEUS_API_SECRET

amadeus = Client(
    client_id=AMADEUS_API_KEY,
    client_secret=AMADEUS_API_SECRET
)
