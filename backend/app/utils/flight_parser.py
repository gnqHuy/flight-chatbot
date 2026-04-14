from datetime import datetime
from app.core.constants import SUPPORTED_AIRLINES

from datetime import datetime

def format_duffel_flight_display(raw_offer: dict, lang: str = "vi") -> dict | None:
    try:
        grand_total = float(raw_offer["total_amount"])
        base_price = float(raw_offer["base_amount"])
        tax_and_fees = float(raw_offer["tax_amount"])
        currency = raw_offer["total_currency"]

        last_ticketing = raw_offer.get("payment_requirements", {}).get("payment_required_by", "N/A")
        validating_airline = raw_offer.get("owner", {}).get("iata_code", "UNKNOWN")
        bookable_seats = "N/A"
        first_slice = raw_offer.get("slices", [{}])[0]
        first_segment = first_slice.get("segments", [{}])[0]
        first_passenger = first_segment.get("passengers", [{}])[0]

        cabin = first_passenger.get("cabin_class", "ECONOMY").upper()
        fare_option = first_slice.get("fare_brand_name", "STANDARD")

        baggages = first_passenger.get("baggages", [])
        checked_qty = sum(bag["quantity"] for bag in baggages if bag["type"] == "checked")
        carry_on_qty = sum(bag["quantity"] for bag in baggages if bag["type"] == "carry_on")

        checked_str = f"{checked_qty} kiện" if checked_qty > 0 else "Không kèm ký gửi"
        cabin_str = f"{carry_on_qty} kiện" if carry_on_qty > 0 else "Không kèm xách tay"

        all_airlines = set()
        parsed_itineraries = []

        for slc in raw_offer.get("slices", []):
            segments = slc.get("segments", [])
            if not segments:
                continue

            first_seg = segments[0]
            last_seg = segments[-1]
            num_stops = len(segments) - 1
            
            raw_duration = slc.get("duration", "")
            formatted_duration = raw_duration.replace("PT", "").replace("H", "h ").replace("M", "m").lower()

            detailed_segments = []
            for i, seg in enumerate(segments):
                # Hãng bay
                carrier_code = seg.get("marketing_carrier", {}).get("iata_code", "XX")
                operating_carrier = seg.get("operating_carrier", {}).get("iata_code", carrier_code)
                all_airlines.add(carrier_code)
                is_codeshare = carrier_code != operating_carrier
                
                layover_time = None
                if i < len(segments) - 1:
                    next_seg = segments[i+1]
                    try:
                        arrival_time = datetime.strptime(seg["arriving_at"], "%Y-%m-%dT%H:%M:%S")
                        next_departure_time = datetime.strptime(next_seg["departing_at"], "%Y-%m-%dT%H:%M:%S")
                        
                        diff = next_departure_time - arrival_time
                        minutes = int(diff.total_seconds() / 60)
                        hours = minutes // 60
                        mins = minutes % 60
                        layover_time = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
                    except Exception as e:
                        print(f"Lỗi tính layover: {e}")

                seg_pax = seg.get("passengers", [{}])[0]
                
                detailed_segments.append({
                    "carrierCode": carrier_code,
                    "operatingCarrier": operating_carrier,
                    "isCodeshare": is_codeshare,
                    "flightNumber": f"{carrier_code}{seg.get('marketing_carrier_flight_number')}",
                    "aircraft": seg.get("aircraft", {}).get("iata_code", "N/A"),
                    "duration": seg.get("duration", "").replace("PT", "").replace("H", "h ").replace("M", "m").lower(),
                    "layoverTime": layover_time,
                    "cabin": seg_pax.get("cabin_class", cabin).upper(),
                    "bookingClass": seg_pax.get("fare_basis_code", "N/A"),
                    "departure": {
                        "iata": seg.get("origin", {}).get("iata_code"),
                        "at": seg["departing_at"],
                        "terminal": seg.get("origin_terminal", "N/A")
                    },
                    "arrival": {
                        "iata": seg.get("destination", {}).get("iata_code"),
                        "at": seg["arriving_at"],
                        "terminal": seg.get("destination_terminal", "N/A")
                    }
                })

            parsed_itineraries.append({
                "duration": formatted_duration,
                "stops": num_stops,
                "flightNumber": f"{first_seg.get('marketing_carrier', {}).get('iata_code')}{first_seg.get('marketing_carrier_flight_number')}",
                "departure": {
                    "iata": first_seg.get("origin", {}).get("iata_code"),
                    "city": first_seg.get("origin", {}).get("city_name"),
                    "at": first_seg["departing_at"],
                    "terminal": first_seg.get("origin_terminal", "N/A")
                },
                "arrival": {
                    "iata": last_seg.get("destination", {}).get("iata_code"),
                    "city": last_seg.get("destination", {}).get("city_name"),
                    "at": last_seg["arriving_at"],
                    "terminal": last_seg.get("destination_terminal", "N/A")
                },
                "segmentDetails": detailed_segments
            })

        return {
            "id": raw_offer["id"],
            "price": grand_total,
            "basePrice": base_price,
            "taxAndFees": tax_and_fees,
            "currency": currency,
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
        print(f"Lỗi parse vé Duffel: {e}")
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