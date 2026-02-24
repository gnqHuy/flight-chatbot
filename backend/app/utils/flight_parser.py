from app.core.i18n_service import i18n

def format_amadeus_flight_display(raw_offer: dict, lang: str = "vi") -> dict | None:
    try:
        itinerary = raw_offer["itineraries"][0]
        segments = itinerary["segments"]
        
        first_segment = segments[0]
        last_segment = segments[-1]
        num_stops = len(segments) - 1 
        
        airlines = list(set([seg["carrierCode"] for seg in segments]))

        price_info = raw_offer["price"]
        fare_details = raw_offer["travelerPricings"][0]["fareDetailsBySegment"][0]
        cabin = fare_details.get("cabin", "ECONOMY")
        checked_bags = fare_details.get("includedCheckedBags", {}).get("weight", 0)

        raw_duration = itinerary["duration"]
        formatted_duration = raw_duration.replace("PT", "").replace("H", "h ").replace("M", "m").lower()

        return {
            "id": raw_offer["id"],
            "price": float(price_info["grandTotal"]),
            "currency": price_info["currency"],
            "cabin": cabin,
            "baggage": f"{checked_bags} kg" if checked_bags else "Không kèm hành lý",
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
            }
        }
    except Exception as e:
        print(f"Lỗi parse vé: {e}")
        return None