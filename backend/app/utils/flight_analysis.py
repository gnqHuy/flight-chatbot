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
    Biến danh sách vé đã được làm sạch thành chuỗi văn bản chuẩn mực 
    để cung cấp cho LLM phân tích (Hỗ trợ cấu trúc Itineraries mới).
    """
    if not parsed_flights:
        return "Không có dữ liệu chi tiết cho các chuyến bay này."
        
    formatted_texts = []
    
    for idx, f in enumerate(parsed_flights, 1):
        try:
            flight_id = f.get('id', str(idx))
            price_str = f"{f.get('price', 0):,.0f} {f.get('currency', 'VND')}".replace(",", ".")
            
            blocks = [
                f"=== [VÉ ID: {flight_id}] ===",
                f"- Giá vé tổng cộng: {price_str}",
                f"- Các hãng hàng không: {', '.join(f.get('airlines', []))}",
                f"- Hạng vé: {f.get('cabin', 'N/A')} (Gói: {f.get('fareOption', 'N/A')})",
                f"- Số ghế trống hiện tại: {f.get('bookableSeats', 'N/A')} ghế",
                f"- Hành lý xách tay: {f.get('cabinBaggage', 'N/A')}",
                f"- Hành lý ký gửi: {f.get('checkedBaggage', 'N/A')}",
                f"- Hạn chót xuất vé: {f.get('lastTicketingDate', 'N/A')}"
            ]
            
            itineraries = f.get('itineraries', [])
            if not itineraries:
                blocks.append("- Lỗi: Không có thông tin hành trình.")
                
            for it_idx, it in enumerate(itineraries):
                direction = "Chiều đi" if it_idx == 0 else "Chiều về"
                
                dep = it.get('departure', {})
                arr = it.get('arrival', {})
                
                blocks.append(f"\n[Hành trình {it_idx + 1}: {direction}]")
                blocks.append(f"  - Tuyến: {dep.get('city', 'N/A')} ({dep.get('iata', 'N/A')}) -> {arr.get('city', 'N/A')} ({arr.get('iata', 'N/A')})")
                blocks.append(f"  - Chuyến bay chính: {it.get('flightNumber', 'N/A')}")
                blocks.append(f"  - Tổng thời gian: {it.get('duration', 'N/A')} | Điểm dừng: {it.get('stops', 0)}")
                
                blocks.append("  * CHI TIẾT CÁC CHẶNG BAY:")
                
                segments = it.get('segments', it.get('segmentDetails', [])) 
                
                for s_idx, seg in enumerate(segments):
                    dep_time = seg.get('departure', {}).get('at', 'N/A').replace('T', ' ')
                    arr_time = seg.get('arrival', {}).get('at', 'N/A').replace('T', ' ')
                    
                    op_carrier = seg.get('operatingCarrier', seg.get('carrierCode', 'N/A'))
                    carrier = seg.get('carrierCode', 'N/A')
                    op_str = f" (Khai thác thực tế bởi: {op_carrier})" if op_carrier != carrier else ""
                    
                    blocks.append(f"    + Chặng {s_idx + 1}: {seg.get('departure', {}).get('iata', 'N/A')} -> {seg.get('arrival', {}).get('iata', 'N/A')}")
                    blocks.append(f"      Mã chuyến: {seg.get('flightNumber', 'N/A')}{op_str}")
                    blocks.append(f"      Khởi hành: {dep_time} - Cổng/Terminal: {seg.get('departure', {}).get('terminal', 'N/A')}")
                    blocks.append(f"      Hạ cánh: {arr_time} - Cổng/Terminal: {seg.get('arrival', {}).get('terminal', 'N/A')}")
                    blocks.append(f"      Thời gian bay: {seg.get('duration', 'N/A')} | Máy bay: {seg.get('aircraft', 'N/A')} | Hạng ghế: {seg.get('cabin', 'N/A')}")
                    blocks.append(f"      Phân loại vé: Class {seg.get('bookingClass', 'N/A')} | Fare Basis: {seg.get('fareBasis', 'N/A')}")
            
            formatted_texts.append("\n".join(blocks))
            
        except Exception as e:
            print(f"Lỗi khi text-format chuyến bay thứ {idx}: {e}")
            formatted_texts.append(f"=== [LỖI TRÍCH XUẤT DỮ LIỆU VÉ ID {f.get('id', idx)}] ===")
            
    return "\n\n".join(formatted_texts)