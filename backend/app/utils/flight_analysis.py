from datetime import datetime

def parse_datetime(dt_str: str) -> str:
    """Chuyển đổi 2026-03-15T05:30:00 thành 05:30 15/03/2026"""
    if not dt_str or dt_str == "N/A": 
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%H:%M %d/%m/%Y")
    except:
        return dt_str

def format_flights_to_text(parsed_flights: list) -> str:
    """
    Biến danh sách vé đã được làm sạch (từ format_amadeus_flight_display) 
    thành chuỗi văn bản chuẩn mực để cung cấp cho LLM phân tích.
    """
    if not parsed_flights:
        return "Không có dữ liệu chi tiết cho các chuyến bay này."
        
    formatted_texts = []
    
    for idx, f in enumerate(parsed_flights, 1):
        try:
            price_str = f"{f['price']:,.0f} {f['currency']}".replace(",", ".")
            
            blocks = [
                f"=== [LỰA CHỌN {idx}] ===",
                f"- Hành trình chính: {f['departure']['city']} ({f['departure']['iata']}) đi {f['arrival']['city']} ({f['arrival']['iata']})",
                f"- Chuyến bay: {f.get('flightNumber', 'N/A')} (Các hãng: {', '.join(f.get('airlines', []))})",
                f"- Giá vé tổng cộng: {price_str}",
                f"- Hạng vé: {f.get('cabin', 'N/A')} (Gói: {f.get('fareOption', 'N/A')})",
                f"- Số ghế trống hiện tại: {f.get('bookableSeats', 'N/A')} ghế",
                f"- Hành lý xách tay: {f.get('cabinBaggage', 'N/A')}",
                f"- Hành lý ký gửi: {f.get('checkedBaggage', 'N/A')}",
                f"- Tổng thời gian di chuyển: {f.get('duration', 'N/A')}",
                f"- Số điểm nối chuyến: {f.get('stops', 0)}",
                f"- Hạn chót xuất vé: {f.get('lastTicketingDate', 'N/A')}"
            ]
            
            blocks.append("\n* CHI TIẾT CÁC CHẶNG BAY:")
            for s_idx, seg in enumerate(f.get('segmentDetails', [])):
                dep_time = parse_datetime(seg['departure']['at'])
                arr_time = parse_datetime(seg['arrival']['at'])
                
                op_carrier = seg.get('operatingCarrier', seg['carrierCode'])
                op_str = f" (Khai thác thực tế bởi: {op_carrier})" if op_carrier != seg['carrierCode'] else ""
                
                blocks.append(f"  + Chặng {s_idx + 1}: {seg['departure']['iata']} -> {seg['arrival']['iata']}")
                blocks.append(f"    Mã chuyến: {seg['flightNumber']}{op_str}")
                blocks.append(f"    Khởi hành: {dep_time} - Cổng/Terminal: {seg['departure'].get('terminal', 'N/A')}")
                blocks.append(f"    Hạ cánh: {arr_time} - Cổng/Terminal: {seg['arrival'].get('terminal', 'N/A')}")
                blocks.append(f"    Thời gian bay: {seg.get('duration', 'N/A')} | Máy bay: {seg.get('aircraft', 'N/A')} | Hạng ghế: {seg.get('cabin', 'N/A')}")
                blocks.append(f"    Phân loại vé: Class {seg.get('bookingClass', 'N/A')} | Fare Basis: {seg.get('fareBasis', 'N/A')}")
            
            formatted_texts.append("\n".join(blocks))
            
        except Exception as e:
            print(f"Lỗi khi text-format chuyến bay thứ {idx}: {e}")
            formatted_texts.append(f"=== [LỖI TRÍCH XUẤT DỮ LIỆU TÙY CHỌN {idx}] ===")
            
    return "\n\n".join(formatted_texts)