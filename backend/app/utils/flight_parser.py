from datetime import datetime
from app.core.i18n_service import i18n
from app.core.constants import SUPPORTED_AIRLINES

def format_amadeus_flight_display(raw_offer: dict, lang: str = "vi") -> dict | None:
    try:
        price_info = raw_offer["price"]
        last_ticketing = raw_offer.get("lastTicketingDate", "N/A")
        validating_airline = raw_offer.get("validatingAirlineCodes", [""])[0]
        bookable_seats = raw_offer.get("numberOfBookableSeats", "N/A")

        grand_total = float(price_info["grandTotal"])
        base_price = float(price_info.get("base", grand_total))
        tax_and_fees = grand_total - base_price

        traveler_pricing = raw_offer["travelerPricings"][0]
        fare_details_list = traveler_pricing.get("fareDetailsBySegment", [])
        
        fare_map = {fare.get("segmentId"): fare for fare in fare_details_list}

        first_fare = fare_details_list[0] if fare_details_list else {}
        cabin = first_fare.get("cabin", "ECONOMY")
        fare_option = traveler_pricing.get("fareOption", "UNKNOWN")

        checked_bags = first_fare.get("includedCheckedBags", {}).get("weight")
        checked_unit = first_fare.get("includedCheckedBags", {}).get("weightUnit", "KG")
        checked_str = f"{checked_bags} {checked_unit}" if checked_bags else "Không kèm ký gửi"

        cabin_bags = first_fare.get("includedCabinBags", {}).get("weight")
        cabin_unit = first_fare.get("includedCabinBags", {}).get("weightUnit", "KG")
        cabin_str = f"{cabin_bags} {cabin_unit}" if cabin_bags else "Không kèm xách tay"

        all_airlines = set()
        parsed_itineraries = []

        for itinerary in raw_offer.get("itineraries", []):
            segments = itinerary.get("segments", [])
            if not segments:
                continue

            first_segment = segments[0]
            last_segment = segments[-1]
            num_stops = len(segments) - 1
            
            raw_duration = itinerary.get("duration", "")
            formatted_duration = raw_duration.replace("PT", "").replace("H", "h ").replace("M", "m").lower()

            detailed_segments = []
            for i, seg in enumerate(segments):
                seg_id = seg.get("id")
                seg_fare = fare_map.get(seg_id, first_fare)
                
                carrier_code = seg["carrierCode"]
                all_airlines.add(carrier_code)
                
                operating_carrier = seg.get("operating", {}).get("carrierCode", carrier_code)
                
                is_codeshare = carrier_code != operating_carrier
                
                layover_time = None
                if i < len(segments) - 1:
                    next_seg = segments[i+1]
                    try:
                        arrival_time = datetime.strptime(seg["arrival"]["at"], "%Y-%m-%dT%H:%M:%S")
                        next_departure_time = datetime.strptime(next_seg["departure"]["at"], "%Y-%m-%dT%H:%M:%S")
                        
                        diff = next_departure_time - arrival_time
                        minutes = int(diff.total_seconds() / 60)
                        hours = minutes // 60
                        mins = minutes % 60
                        layover_time = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
                    except Exception as e:
                        print(f"Lỗi tính layover: {e}")
                
                detailed_segments.append({
                    "carrierCode": carrier_code,
                    "operatingCarrier": operating_carrier,
                    "isCodeshare": is_codeshare,
                    "flightNumber": f"{carrier_code}{seg['number']}",
                    "aircraft": seg.get("aircraft", {}).get("code", "N/A"),
                    "duration": seg.get("duration", "").replace("PT", "").replace("H", "h ").replace("M", "m").lower(),
                    "layoverTime": layover_time,
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

            parsed_itineraries.append({
                "duration": formatted_duration,
                "stops": num_stops,
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
            })

        return {
            "id": raw_offer["id"],
            "price": grand_total,
            "basePrice": base_price,
            "taxAndFees": tax_and_fees,
            "currency": price_info["currency"],
            "cabin": cabin,
            "fareOption": fare_option,
            "bookableSeats": bookable_seats,
            "lastTicketingDate": last_ticketing,
            "validatingAirline": validating_airline,
            "checkedBaggage": checked_str,
            "cabinBaggage": cabin_str,
            "airlines": list(all_airlines),
            "itineraries": parsed_itineraries
        }
        
    except Exception as e:
        print(f"Lỗi parse vé: {e}")
        return None

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