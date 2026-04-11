import json
from typing import Optional, List, Any
from amadeus import Client, ResponseError
import requests
from app.core.config import AMADEUS_API_KEY, AMADEUS_API_SECRET, DUFFEL_ACCESS_TOKEN, DUFFEL_ACCESS_TOKEN
from app.core.constants import MAX_FLIGHTS_RETURNED
from app.utils.flight_parser import format_duffel_flight_display 

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
            slices = [{
                "origin": origin,
                "destination": destination,
                "departure_date": departureDate
            }]

            if returnDate and roundTrip:
                slices.append({
                    "origin": destination,
                    "destination": origin,
                    "departure_date": returnDate
                })

            # 2. Khởi tạo Passengers (Hành khách)
            passengers = []
            
            safe_adults = max(1, int(adults) if adults is not None else 1)
            for _ in range(safe_adults):
                passengers.append({"type": "adult"})
            
            safe_children = int(children) if children is not None else 0
            for _ in range(safe_children):
                passengers.append({"type": "child"})
            
            safe_infants = int(infants) if infants is not None else 0
            for _ in range(safe_infants):
                passengers.append({"type": "infant_without_seat"}) # Duffel dùng keyword này

            # 3. Xử lý hạng ghế (Cabin Class)
            duffel_cabin = None
            if travelClass:
                tc_value = travelClass.value if hasattr(travelClass, 'value') else str(travelClass).upper()
                mapping = {
                    "ECONOMY": "economy",
                    "PREMIUM_ECONOMY": "premium_economy",
                    "BUSINESS": "business",
                    "FIRST": "first"
                }
                duffel_cabin = mapping.get(tc_value, "economy") 

            payload_data = {
                "slices": slices,
                "passengers": passengers,
            }
            if duffel_cabin:
                payload_data["cabin_class"] = duffel_cabin

            body = {"data": payload_data}

            print(f"--- [DUFFEL POST API] Payload: {json.dumps(body, indent=2)} ---")

            token = DUFFEL_ACCESS_TOKEN
            url = "https://api.duffel.com/air/offer_requests?return_offers=true"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Duffel-Version": "v2",
                "Authorization": f"Bearer {token}"
            }

            response = requests.post(url, json=body, headers=headers)
            response.raise_for_status()
            
            response_data = response.json()
            raw_offers = response_data.get("data", {}).get("offers", [])

            if not raw_offers:
                return []

            if includedAirlines:
                valid_airlines = set(a.upper() for a in includedAirlines)
                filtered_offers = []
                for offer in raw_offers:
                    owner_code = offer.get("owner", {}).get("iata_code", "").upper()
                    if owner_code in valid_airlines:
                        filtered_offers.append(offer)
                raw_offers = filtered_offers

            raw_offers = raw_offers[:max_offers]

            formatted_flights = []
            for raw_flight in raw_offers:
                clean_flight = format_duffel_flight_display(raw_flight, lang=lang)
                if clean_flight:
                    formatted_flights.append(clean_flight)

            return formatted_flights

        except requests.exceptions.HTTPError as e:
            error_detail = str(e)
            try:
                error_body = response.json()
                if "errors" in error_body and len(error_body["errors"]) > 0:
                    error_detail = error_body["errors"][0].get("message", error_detail)
            except Exception:
                pass
            print(f"❌ [DUFFEL ERROR]: {error_detail}")
            raise Exception(f"Lỗi API Duffel: {error_detail}")

        except Exception as e:
            print(f"❌ [SYSTEM ERROR]: {e}")
            raise Exception(f"Lỗi hệ thống khi tìm vé: {str(e)}")
        
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