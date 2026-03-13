import os
import json
from typing import Optional, List, Any
from amadeus import Client, ResponseError
from app.utils.flight_parser import format_amadeus_flight_display 

class FlightService:
    def __init__(self):
        self.amadeus = Client(
            client_id=os.getenv('AMADEUS_API_KEY'),
            client_secret=os.getenv('AMADEUS_API_SECRET')
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
        includedAirlines: Optional[List[str]] = None,
        nonStop: Optional[bool] = None,
        travelClass: Any = None,
        maxPrice: Optional[int] = None,
        start_hour: Optional[int] = None,
        end_hour: Optional[int] = None,
        max_offers: int = 50,
        lang: str = "vi"
    ):
        try:
            dep_range = {"date": departureDate}
            
            if start_hour is not None and end_hour is not None:
                mid_hour = (start_hour + end_hour) // 2
                window = max(1, (end_hour - start_hour) // 2)
                
                dep_range["time"] = f"{mid_hour:02d}:00:00"
                dep_range["timeWindow"] = f"{window}H"

            origin_destinations = [{
                "id": "1",
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDateTimeRange": dep_range
            }]

            if returnDate:
                origin_destinations.append({
                    "id": "2",
                    "originLocationCode": destination,
                    "destinationLocationCode": origin,
                    "departureDateTimeRange": {"date": returnDate}
                })

            flight_filters = {}

            if travelClass:
                od_ids = ["1"]
                if returnDate:
                    od_ids.append("2")

                tc_value = travelClass.value if hasattr(travelClass, 'value') else str(travelClass).upper()
                
                flight_filters["cabinRestrictions"] = [{
                    "cabin": tc_value,
                    "coverage": "MOST_SEGMENTS",
                    "originDestinationIds": od_ids
                }]

            carrier_restrictions = {}
            if includedAirlines:
                carrier_restrictions["includedCarrierCodes"] = includedAirlines

            if carrier_restrictions:
                flight_filters["carrierRestrictions"] = carrier_restrictions

            if nonStop is not None:
                flight_filters["connectionRestriction"] = {"maxNumberOfConnections": 0 if nonStop else 2}

            if maxPrice:
                flight_filters["priceRestriction"] = {"maxPrice": maxPrice}

            search_criteria = {
                "maxFlightOffers": max_offers  
            }
            if flight_filters:
                search_criteria["flightFilters"] = flight_filters

            travelers = []            
            current_id = 1
            adult_ids = []
            for _ in range(adults):
                travelers.append({"id": str(current_id), "travelerType": "ADULT"})
                adult_ids.append(str(current_id))
                current_id += 1
            
            for _ in range(children):
                travelers.append({"id": str(current_id), "travelerType": "CHILD"})
                current_id += 1
            
            for i in range(infants):
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
            if hasattr(error, 'response') and error.response and error.response.result:
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