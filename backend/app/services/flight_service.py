import json
from typing import Optional, List, Any
from amadeus import Client, ResponseError
from app.core.config import AMADEUS_API_KEY, AMADEUS_API_SECRET
from app.core.constants import MAX_FLIGHTS_RETURNED
from app.utils.flight_parser import format_amadeus_flight_display 

class FlightService:
    def __init__(self):
        self.amadeus = Client(
            client_id=AMADEUS_API_KEY,
            client_secret=AMADEUS_API_SECRET
        )

    def search_flights(
        self, 
        origin: str, 
        destination: str, 
        departureDate: str, 
        returnDate: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        roundTrip: bool = False,
        includedAirlines: Optional[List[str]] = None,
        travelClass: Optional[str] = None,
        max_offers: int = MAX_FLIGHTS_RETURNED,
        lang: str = "vi"
    ):
        try:
            origin_destinations = [{
                "id": "1",
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDateTimeRange": {"date": departureDate}
            }]

            if returnDate and roundTrip:
                origin_destinations.append({
                    "id": "2",
                    "originLocationCode": destination,
                    "destinationLocationCode": origin,
                    "departureDateTimeRange": {"date": returnDate}
                })

            flight_filters = {}

            if travelClass:
                tc_value = travelClass.value if hasattr(travelClass, 'value') else str(travelClass).upper()
                
                valid_cabins = ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"]
                
                if tc_value in valid_cabins:
                    od_ids = ["1"]
                    if roundTrip and returnDate:
                        od_ids.append("2")

                    flight_filters["cabinRestrictions"] = [{
                        "cabin": tc_value,
                        "coverage": "MOST_SEGMENTS",
                        "originDestinationIds": od_ids
                    }]

            if includedAirlines:
                flight_filters["carrierRestrictions"] = {
                    "includedCarrierCodes": includedAirlines
                }

            search_criteria = {
                "maxFlightOffers": max_offers  
            }
            if flight_filters:
                search_criteria["flightFilters"] = flight_filters

            travelers = []            
            current_id = 1
            adult_ids = []
            
            safe_adults = max(1, int(adults) if adults is not None else 1)
            for _ in range(safe_adults):
                t_id = str(current_id)
                travelers.append({"id": t_id, "travelerType": "ADULT"})
                adult_ids.append(t_id)
                current_id += 1
            
            safe_children = int(children) if children is not None else 0
            for _ in range(safe_children):
                travelers.append({"id": str(current_id), "travelerType": "CHILD"})
                current_id += 1
            
            safe_infants = int(infants) if infants is not None else 0
            for i in range(safe_infants):
                assoc_id = adult_ids[i] if i < len(adult_ids) else adult_ids[0]
                travelers.append({
                    "id": str(current_id), 
                    "travelerType": "HELD_INFANT", 
                    "associatedAdultId": assoc_id
                })
                current_id += 1

            body = {
                "currencyCode": "VND",
                "originDestinations": origin_destinations,
                "travelers": travelers,
                "sources": ["GDS"],
                "searchCriteria": search_criteria
            }

            print(f"--- [AMADEUS POST API] Payload: {json.dumps(body, indent=2)} ---")
            
            response = self.amadeus.shopping.flight_offers_search.post(body)

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
            if hasattr(error, 'response') and error.response and getattr(error.response, 'result', None):
                errors = error.response.result.get('errors', [])
                if errors:
                    error_detail = errors[0].get('detail', str(error))
                    
            raise Exception(f"Lỗi API: {error_detail}")

    def get_price_metrics(self, origin: str, destination: str, departureDate: str) -> list:
        """Gọi API Amadeus Itinerary Price Metrics để lấy dữ liệu phân tích giá"""
        try:
            response = self.amadeus.analytics.itinerary_price_metrics.get(
                originIataCode=origin,
                destinationIataCode=destination,
                departureDate=departureDate,
                currencyCode="VND"
            )
            if response.data and len(response.data) > 0:
                return response.data[0].get("priceMetrics", [])
            return []
        except Exception as e:
            print(f"[LỖI AMADEUS PRICE METRICS]: {e}")
            return []
        
flight_service = FlightService()