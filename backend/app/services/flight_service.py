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
        includedAirlines: Optional[List[str]] = None,
        excludedAirlines: Optional[List[str]] = None,
        nonStop: Optional[bool] = None,
        travelClass: Any = None,
        maxPrice: Optional[int] = None,
        start_hour: Optional[int] = None,
        end_hour: Optional[int] = None,
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
                tc_value = travelClass.value if hasattr(travelClass, 'value') else str(travelClass).upper()
                flight_filters["cabinRestrictions"] = [{"cabin": tc_value, "coverage": "MOST_SEGMENTS"}]

            carrier_restrictions = {}
            if includedAirlines:
                carrier_restrictions["includedCarrierCodes"] = includedAirlines
            if excludedAirlines:
                carrier_restrictions["excludedCarrierCodes"] = excludedAirlines
            if carrier_restrictions:
                flight_filters["carrierRestrictions"] = carrier_restrictions

            if nonStop is not None:
                flight_filters["connectionRestriction"] = {"maxNumberOfConnections": 0 if nonStop else 2}

            if maxPrice:
                flight_filters["priceRestriction"] = {"maxPrice": maxPrice}

            search_criteria = {
                "maxFlightOffers": 20  
            }
            if flight_filters:
                search_criteria["flightFilters"] = flight_filters

            body = {
                "currencyCode": "VND",
                "originDestinations": origin_destinations,
                "travelers": [{"id": str(i+1), "travelerType": "ADULT"} for i in range(adults)],
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

flight_service = FlightService()