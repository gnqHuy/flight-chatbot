'use client';

import { FlightOffer } from '@/types/FlightOffer';
import React from 'react';
import { Plane, Briefcase, BaggageClaim, AlertCircle, Clock, Sparkles } from 'lucide-react';

type Props = {
  flight: FlightOffer;
  onAskAI: (prompt: string) => void;
};

const FlightOfferCard: React.FC<Props> = ({ flight, onAskAI }) => {
  const formatTime = (time: string) => {
    if (!time) return '--:--';
    return new Date(time).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  };

  // 🌟 CẬP NHẬT: Tự động quy đổi giá tiền sang VND
  const formatPrice = (price: number, currency: string) => {
    let finalPrice = price;
    
    // Tỷ giá giả định (Bạn có thể điều chỉnh hoặc truyền từ API/Config vào)
    const USD_TO_VND_RATE = 25450; 

    // Nếu tiền tệ không phải VND, tự động quy đổi (Ví dụ mặc định ngoại tệ là USD)
    if (currency && currency.toUpperCase() !== 'VND') {
      finalPrice = price * USD_TO_VND_RATE;
    }

    return new Intl.NumberFormat('vi-VN', { 
      style: 'currency', 
      currency: 'VND',
      maximumFractionDigits: 0 // Bỏ số thập phân cho chuẩn tiền Việt
    }).format(finalPrice);
  };

  const formatDuration = (ptString: string) => {
    if (!ptString) return '--';
    return ptString.replace('PT', '').replace('H', 'h ').replace('M', 'm').toLowerCase();
  };

  // Vẫn giữ lại flightNumbers để AI hiển thị trong câu trả lời cho tự nhiên
  const allFlightNumbers = flight.itineraries?.map((it) => it.flightNumber).join(' và ') || '';

  return (
    <div className="group relative flex w-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-lg sm:flex-row">
      {/* CỘT TRÁI: CHI TIẾT CHUYẾN BAY */}
      <div className="flex flex-1 flex-col justify-center p-5 sm:p-6">
        <div className="flex flex-col gap-6">
          {flight.itineraries?.map((itinerary, index) => {
            const segments = itinerary.segmentDetails || [];
            const layovers = segments.filter((seg) => seg.layoverTime);
            const hasCodeshare = segments.some((seg) => seg.isCodeshare);

            return (
              <div key={index} className="flex flex-col relative">
                {/* Hiển thị nhãn Chiều đi / Chiều về nếu là khứ hồi */}
                {flight.itineraries.length > 1 && (
                  <span className="mb-3 flex items-center gap-1.5 text-[11px] font-bold tracking-widest text-blue-600/80 uppercase">
                    {index === 0 ? <Plane className="h-3 w-3 -rotate-45" /> : <Plane className="h-3 w-3 rotate-45" />}
                    {index === 0 ? 'Chiều đi' : 'Chiều về'}
                  </span>
                )}

                <div className="flex flex-row items-center justify-between gap-2">
                  {/* Nơi đi */}
                  <div className="flex w-15 flex-col items-start sm:w-20">
                    <p className="text-2xl font-bold tracking-tight text-slate-900">
                      {formatTime(itinerary.departure.at)}
                    </p>
                    <p className="mt-0.5 text-sm font-semibold text-slate-500">
                      {itinerary.departure.iata}
                    </p>
                  </div>

                  {/* Thông tin đường bay */}
                  <div className="flex flex-1 flex-col items-center px-2">
                    <div className="mb-1.5 flex items-center gap-1 text-[11px] font-medium text-slate-500">
                      <Clock className="h-3 w-3" />
                      {formatDuration(itinerary.duration)}
                    </div>

                    {/* Timeline */}
                    <div className="relative flex w-full items-center py-2">
                      <div className="h-[2px] w-full rounded-full bg-slate-200 group-hover:bg-blue-100 transition-colors"></div>
                      <div className="absolute left-1/2 flex -translate-x-1/2 items-center justify-center bg-white px-2">
                        <Plane className="h-4 w-4 text-blue-400 group-hover:text-blue-500 transition-colors" />
                      </div>
                    </div>

                    <span className="mt-1 text-center text-[11px] font-semibold text-slate-500">
                      {itinerary.stops === 0 ? 'Bay thẳng' : <span className="text-amber-500">{`${itinerary.stops} điểm dừng`}</span>}
                    </span>

                    {/* Badge Flight Number */}
                    <span className="mt-2 rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-bold tracking-wider text-slate-600">
                      {itinerary.flightNumber}
                    </span>

                    {/* THỜI GIAN NỐI CHUYẾN */}
                    {layovers.length > 0 && (
                      <div className="mt-2 flex flex-wrap justify-center gap-1">
                        {layovers.map((layover, idx) => (
                          <span
                            key={idx}
                            className="flex items-center gap-1 rounded border border-amber-200 bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-700"
                          >
                            <Clock className="h-2.5 w-2.5" /> Dừng {layover.layoverTime} tại {layover.arrival.iata}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* CẢNH BÁO CODESHARE */}
                    {hasCodeshare && (
                      <div className="mt-1.5 flex justify-center">
                        <span
                          className="flex items-center gap-1 rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10px] font-medium text-slate-600"
                          title="Chuyến bay được khai thác bởi hãng hàng không đối tác"
                        >
                          <AlertCircle className="h-2.5 w-2.5" /> Bay liên danh
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Nơi đến */}
                  <div className="flex w-15 flex-col items-end sm:w-20">
                    <p className="text-2xl font-bold tracking-tight text-slate-900">
                      {formatTime(itinerary.arrival.at)}
                    </p>
                    <p className="mt-0.5 text-sm font-semibold text-slate-500">
                      {itinerary.arrival.iata}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Thông tin Hành lý */}
        <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-4">
          <div className="flex items-center gap-1.5 rounded-lg bg-slate-50 px-2.5 py-1.5 text-[12px] font-medium text-slate-600 border border-slate-100">
            <Briefcase className="h-3.5 w-3.5 text-slate-600" />
            <span>Xách tay: <span className="font-semibold text-slate-700">{flight.cabinBaggage || 'Không rõ'}</span></span>
          </div>
          <div className="flex items-center gap-1.5 rounded-lg bg-slate-50 px-2.5 py-1.5 text-[12px] font-medium text-slate-600 border border-slate-100">
            <BaggageClaim className="h-3.5 w-3.5 text-slate-600" />
            <span>Ký gửi: <span className="font-semibold text-slate-700">{flight.checkedBaggage || 'Không có'}</span></span>
          </div>
        </div>
      </div>

      {/* CỘT PHẢI: GIÁ TIỀN & ACTION */}
      <div className="flex flex-col items-center justify-center bg-slate-50/50 p-5 sm:w-64 border-t sm:border-t-0 sm:border-l border-slate-100">
        <div className="mb-2 flex flex-col items-center text-center">
          <span className="text-[14px] font-bold tracking-widest text-black uppercase">
            {flight.cabin || 'Phổ thông'}
          </span>
          {flight.fareOption && (
            <span className="mt-0.5 inline-block rounded-full bg-blue-100/50 px-2 py-0.5 text-[12px] font-semibold text-blue-600">
              Gói {flight.fareOption}
            </span>
          )}
        </div>

        <p className="text-2xl font-extrabold text-rose-500 tracking-tight">
          {formatPrice(flight.price, flight.currency)}
        </p>

        {/* TÁCH THUẾ PHÍ CHI TIẾT */}
        {/* {(flight.basePrice > 0 || flight.taxAndFees > 0) && (
          <div className="mt-3 w-full space-y-1.5 rounded-lg bg-white p-2.5 text-[12px] font-medium text-slate-500 shadow-sm border border-slate-100">
            <div className="flex justify-between items-center">
              <span>Giá vé cơ bản</span>
              <span className="text-slate-700">{formatPrice(flight.basePrice, flight.currency)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Thuế & Phí</span>
              <span className="text-slate-700">{formatPrice(flight.taxAndFees, flight.currency)}</span>
            </div>
          </div>
        )} */}

        <button
          onClick={(e) => {
            e.stopPropagation();
            onAskAI(
              `Phân tích ưu nhược điểm và hành lý của chuyến bay ${allFlightNumbers} (Hãng: ${
                flight.airlines?.join(', ') || 'N/A'
              }).`
            );
          }}
          className="group/btn mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-3 text-sm font-bold text-blue-700 transition-all duration-300 hover:from-blue-600 hover:to-indigo-600 hover:text-white hover:shadow-md hover:shadow-blue-200"
        >
          <Sparkles className="h-4 w-4 text-blue-500 group-hover/btn:text-white transition-colors" />
          Hỏi AI chuyến này
        </button>
      </div>
    </div>
  );
};

export default FlightOfferCard;