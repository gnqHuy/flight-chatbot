import os
from amadeus import Client, ResponseError

class FlightService:
    def __init__(self):
        self.amadeus = Client(
            client_id=os.getenv('AMADEUS_API_KEY'),
            client_secret=os.getenv('AMADEUS_API_SECRET')
        )

    def search_flights(self, origin: str, destination: str, departureDate: str):
        """
        Hàm thuần túy: Nhận input -> Trả về List chuyến bay hoặc None
        """
        try:
            response = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departureDate,
                adults=1,
                max=5
            )

            if not response.data:
                return []

            formatted_flights = []
            for flight in response.data:
                offer = {
                    "id": flight['id'],
                    "price": flight['price']['total'],
                    "currency": flight['price']['currency'],
                    "airline": flight['validatingAirlineCodes'][0],
                    "itineraries": []
                }
                for itinerary in flight['itineraries']:
                    segments = []
                    for segment in itinerary['segments']:
                        segments.append({
                            "departure_at": segment['departure']['at'],
                            "arrival_at": segment['arrival']['at'],
                            "departure_code": segment['departure']['iataCode'], 
                            "arrival_at": segment['arrival']['at'],
                            "arrival_code": segment['arrival']['iataCode'],
                            "carrier": segment['carrierCode'],
                            "flight_number": segment['number']
                        })
                    offer["itineraries"].append(segments)
                formatted_flights.append(offer)
            
            return response.data

        except ResponseError as error:
            print(f"Amadeus Service Error: {error}")
            raise Exception(f"Lỗi API: {error.response.result.get('errors', [{}])[0].get('detail', str(error))}")

flight_service = FlightService()