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
    để cung cấp cho LLM phân tích (Đã tích hợp Thuế phí, Nối chuyến, Codeshare).
    """
    if not parsed_flights:
        return "Không có dữ liệu chi tiết cho các chuyến bay này."
        
    formatted_texts = []
    
    def fmt_price(p):
        if isinstance(p, (int, float)):
            return f"{p:,.2f}".rstrip('0').rstrip('.') if p % 1 != 0 else f"{p:,.0f}"
        return str(p)
    
    for idx, f in enumerate(parsed_flights, 1):
        try:
            flight_id = f.get('id') or str(idx)
            
            currency = f.get('currency') or 'VND'
            price_str = f"{fmt_price(f.get('price', 0))} {currency}".replace(",", ".")
            base_str = f"{fmt_price(f.get('basePrice', 0))} {currency}".replace(",", ".")
            tax_str = f"{fmt_price(f.get('taxAndFees', 0))} {currency}".replace(",", ".")
            
            airlines = f.get('airlines') or []
            
            blocks = [
                f"=== [VÉ: {flight_id} cũa Hãng bay: {', '.join(airlines)}] ===",
                f"- Giá vé tổng cộng: {price_str} (Giá gốc: {base_str} | Thuế/Phí: {tax_str})",
                f"- Các hãng hàng không: {', '.join(airlines)}",
                f"- Hạng vé: {f.get('cabin') or 'N/A'} (Gói: {f.get('fareOption') or 'N/A'})",
                f"- Số ghế trống hiện tại: {f.get('bookableSeats') or 'N/A'} ghế",
                f"- Hành lý xách tay: {f.get('cabinBaggage') or 'N/A'}",
                f"- Hành lý ký gửi: {f.get('checkedBaggage') or 'N/A'}",
                f"- Hạn chót xuất vé: {f.get('lastTicketingDate') or 'N/A'}"
            ]
            
            itineraries = f.get('itineraries') or []
            if not itineraries:
                blocks.append("- Lỗi: Không có thông tin hành trình.")
                
            for it_idx, it in enumerate(itineraries):
                direction = "Chiều đi" if it_idx == 0 else "Chiều về"
                
                dep = it.get('departure') or {}
                arr = it.get('arrival') or {}
                
                blocks.append(f"\n[Hành trình {it_idx + 1}: {direction}]")
                blocks.append(f"  - Tuyến: {dep.get('city') or 'N/A'} ({dep.get('iata') or 'N/A'}) -> {arr.get('city') or 'N/A'} ({arr.get('iata') or 'N/A'})")
                blocks.append(f"  - Chuyến bay chính: {it.get('flightNumber') or 'N/A'}")
                blocks.append(f"  - Tổng thời gian: {it.get('duration') or 'N/A'} | Điểm dừng: {it.get('stops', 0)}")
                
                blocks.append("  * CHI TIẾT CÁC CHẶNG BAY:")
                
                segments = it.get('segmentDetails') or []
                
                for s_idx, seg in enumerate(segments):
                    seg_dep = seg.get('departure') or {}
                    seg_arr = seg.get('arrival') or {}
                    
                    dep_time = (seg_dep.get('at') or 'N/A').replace('T', ' ')
                    arr_time = (seg_arr.get('at') or 'N/A').replace('T', ' ')
                    
                    is_codeshare = seg.get('isCodeshare', False)
                    op_carrier = seg.get('operatingCarrier') or 'N/A'
                    op_str = f" (⚠️ Khai thác thực tế bởi hãng: {op_carrier})" if is_codeshare else ""
                    
                    term_dep = seg_dep.get('terminal') or 'N/A'
                    term_arr = seg_arr.get('terminal') or 'N/A'
                    
                    blocks.append(f"    + Chặng {s_idx + 1}: {seg_dep.get('iata') or 'N/A'} -> {seg_arr.get('iata') or 'N/A'}")
                    blocks.append(f"      Mã chuyến: {seg.get('flightNumber') or 'N/A'}{op_str}")
                    blocks.append(f"      Khởi hành: {dep_time} - Cổng/Terminal: {term_dep}")
                    blocks.append(f"      Hạ cánh: {arr_time} - Cổng/Terminal: {term_arr}")
                    blocks.append(f"      Thời gian bay: {seg.get('duration') or 'N/A'} | Máy bay: {seg.get('aircraft') or 'N/A'} | Hạng ghế: {seg.get('cabin') or 'N/A'}")
                    blocks.append(f"      Phân loại vé: Class {seg.get('bookingClass') or 'N/A'} | Fare Basis: {seg.get('fareBasis') or 'N/A'}")
                    
                    layover = seg.get('layoverTime')
                    if layover:
                        blocks.append(f"      ⏳ TRẠM DỪNG: Khách chờ nối chuyến tại {seg_arr.get('iata') or 'N/A'} trong {layover}")
            
            formatted_texts.append("\n".join(blocks))
            
        except Exception as e:
            print(f"Lỗi khi text-format chuyến bay thứ {idx}: {e}")
            formatted_texts.append(f"=== [LỖI TRÍCH XUẤT DỮ LIỆU VÉ ID {f.get('id', idx)}] ===")
            
    return "\n\n".join(formatted_texts)