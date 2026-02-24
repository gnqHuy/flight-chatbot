import os
from amadeus import Client, ResponseError
from app.utils.flight_parser import format_amadeus_flight_display # Import parser vào đây

class FlightService:
    def __init__(self):
        self.amadeus = Client(
            client_id=os.getenv('AMADEUS_API_KEY'),
            client_secret=os.getenv('AMADEUS_API_SECRET')
        )

    def search_flights(self, origin: str, destination: str, departureDate: str, lang: str = "vi"):
        try:
            response = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departureDate,
                adults=1,
                max=5,
                currencyCode='VND'
            )

            if not response.data:
                return []

            formatted_flights = []
            for raw_flight in response.data:
                clean_flight = format_amadeus_flight_display(raw_flight, lang=lang)
                if clean_flight:
                    formatted_flights.append(clean_flight)

            return formatted_flights

        except ResponseError as error:
            print(f"Amadeus Service Error: {error}")
            error_detail = str(error)
            if hasattr(error, 'response') and error.response and error.response.result:
                errors = error.response.result.get('errors', [])
                if errors:
                    error_detail = errors[0].get('detail', str(error))
                    
            raise Exception(f"Lỗi API: {error_detail}")

flight_service = FlightService()