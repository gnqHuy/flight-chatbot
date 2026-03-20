from app.core.i18n_service import i18n
from app.core.constants import SUPPORTED_AIRLINES

def format_amadeus_flight_display(raw_offer: dict, lang: str = "vi") -> dict | None:
    try:
        itinerary = raw_offer["itineraries"][0]
        segments = itinerary["segments"]
        
        first_segment = segments[0]
        last_segment = segments[-1]
        num_stops = len(segments) - 1 
        
        airlines = list(set([seg["carrierCode"] for seg in segments]))

        price_info = raw_offer["price"]
        
        last_ticketing = raw_offer.get("lastTicketingDate", "N/A")
        validating_airline = raw_offer.get("validatingAirlineCodes", [""])[0]
        bookable_seats = raw_offer.get("numberOfBookableSeats", "N/A")

        traveler_pricing = raw_offer["travelerPricings"][0]
        fare_details = traveler_pricing["fareDetailsBySegment"][0]
        
        cabin = fare_details.get("cabin", "ECONOMY")
        fare_option = traveler_pricing.get("fareOption", "UNKNOWN")

        checked_bags = fare_details.get("includedCheckedBags", {}).get("weight")
        checked_unit = fare_details.get("includedCheckedBags", {}).get("weightUnit", "KG")
        checked_str = f"{checked_bags} {checked_unit}" if checked_bags else "Không kèm ký gửi"

        cabin_bags = fare_details.get("includedCabinBags", {}).get("weight")
        cabin_unit = fare_details.get("includedCabinBags", {}).get("weightUnit", "KG")
        cabin_str = f"{cabin_bags} {cabin_unit}" if cabin_bags else "Không kèm xách tay"

        raw_duration = itinerary["duration"]
        formatted_duration = raw_duration.replace("PT", "").replace("H", "h ").replace("M", "m").lower()

        detailed_segments = []
        for idx, seg in enumerate(segments):
            seg_fare = traveler_pricing["fareDetailsBySegment"][idx] if idx < len(traveler_pricing["fareDetailsBySegment"]) else fare_details
            
            operating_carrier = seg.get("operating", {}).get("carrierCode", seg["carrierCode"])
            
            detailed_segments.append({
                "carrierCode": seg["carrierCode"],
                "operatingCarrier": operating_carrier,
                "flightNumber": f"{seg['carrierCode']}{seg['number']}",
                "aircraft": seg.get("aircraft", {}).get("code", "N/A"),
                "duration": seg.get("duration", "").replace("PT", "").replace("H", "h ").replace("M", "m").lower(),
                "cabin": seg_fare.get("cabin", cabin),
                "bookingClass": seg_fare.get("class", "N/A"),
                "fareBasis": seg_fare.get("fareBasis", "N/A"),
                "departure": {
                    "iata": seg["departure"]["iataCode"],
                    "at": seg["departure"]["at"],
                    "terminal": seg["departure"].get("terminal", "N/A")
                },
                "arrival": {
                    "iata": seg["arrival"]["iataCode"],
                    "at": seg["arrival"]["at"],
                    "terminal": seg["arrival"].get("terminal", "N/A")
                }
            })

        return {
            "id": raw_offer["id"],
            "price": float(price_info["grandTotal"]),
            "currency": price_info["currency"],
            "cabin": cabin,
            "fareOption": fare_option,
            "bookableSeats": bookable_seats,
            "lastTicketingDate": last_ticketing,
            "validatingAirline": validating_airline,
            "checkedBaggage": checked_str,
            "cabinBaggage": cabin_str,
            "duration": formatted_duration,
            "stops": num_stops,
            "airlines": airlines, 
            "flightNumber": f"{first_segment['carrierCode']}{first_segment['number']}", 
            "departure": {
                "iata": first_segment["departure"]["iataCode"], 
                "city": i18n.get_city(first_segment["departure"]["iataCode"], lang), 
                "at": first_segment["departure"]["at"], 
                "terminal": first_segment["departure"].get("terminal", "N/A")
            },
            "arrival": {
                "iata": last_segment["arrival"]["iataCode"], 
                "city": i18n.get_city(last_segment["arrival"]["iataCode"], lang),
                "at": last_segment["arrival"]["at"], 
                "terminal": last_segment["arrival"].get("terminal", "N/A")
            },
            "segmentDetails": detailed_segments
        }
    except Exception as e:
        print(f"Lỗi parse vé: {e}")
        return None
    
def get_final_airlines(user_prefs: dict) -> list:
    """
    Tính toán danh sách hãng bay cuối cùng từ State đã được merge hoàn chỉnh.
    """
    included = user_prefs.get("includedAirlines", [])
    excluded = user_prefs.get("excludedAirlines", [])
    
    active_airlines = set(SUPPORTED_AIRLINES)
    
    if included:
        active_airlines = set(included)
    if excluded:
        active_airlines = active_airlines - set(excluded)
        
    return list(active_airlines)

def group_flights_by_airline(flights: list, final_airlines: list) -> dict:
    """
    Nhóm một mảng phẳng các chuyến bay thành Dictionary chia theo hãng (Tab).
    """
    grouped_flights = {tab: [] for tab in final_airlines}
    for f in flights:
        fn = str(f.get("flightNumber", "")).upper()
        airline_code = fn[:2] 
        if airline_code in grouped_flights:
            grouped_flights[airline_code].append(f)
    return grouped_flights