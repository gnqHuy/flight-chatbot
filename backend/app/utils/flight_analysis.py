
def analyze_flights_for_comparison(flights: list) -> str:
    if not flights: return ""
    try:
        def get_price(f):
            p = f.get('price', {})
            return float(p.get('total', 0)) if isinstance(p, dict) else float(f.get('price', 0))

        def get_airline(f):
            airlines_list = f.get('airlines')
            if airlines_list and isinstance(airlines_list, list) and len(airlines_list) > 0:
                return airlines_list[0]
                
            if f.get('airline'): return f.get('airline')
            if f.get('airlineCode'): return f.get('airlineCode')
            
            val_airlines = f.get('validatingAirlineCodes')
            if val_airlines and isinstance(val_airlines, list) and len(val_airlines) > 0:
                return val_airlines[0]
                
            try:
                itineraries = f.get('itineraries', [])
                if itineraries:
                    segments = itineraries[0].get('segments', [])
                    if segments:
                        return segments[0].get('carrierCode', 'Unknown')
            except Exception:
                pass
                
            return 'Unknown'

        sorted_flights = sorted(flights, key=get_price)
        cheapest = sorted_flights[0]
        
        airline_cheapest = {}
        for f in sorted_flights:
            airline = get_airline(f)
            if airline not in airline_cheapest:
                airline_cheapest[airline] = f

        report = ["[BÁO CÁO PHÂN TÍCH SO SÁNH]"]
        report.append(f"- RẺ NHẤT TOÀN CHUYẾN: Hãng {get_airline(cheapest)}, Giá: {get_price(cheapest):,.0f} VND")
        report.append("- RẺ NHẤT THEO TỪNG HÃNG:")
        for airline, f in airline_cheapest.items():
            report.append(f"  + {airline}: {get_price(f):,.0f} VND")
            
        return "\n".join(report)
        
    except Exception as e:
        print(f"Lỗi phân tích so sánh: {e}")
        return "Hệ thống đang đối chiếu dữ liệu các chuyến bay..."