'use client';

import { FlightOffer } from '@/types/FlightOffer';
import React from 'react';

type Props = {
  flight: FlightOffer;
  onAskAI: (prompt: string) => void;
};

const FlightOfferCard: React.FC<Props> = ({ flight, onAskAI }) => {
  const formatTime = (time: string) => {
    if (!time) return '--:--';
    return new Date(time).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  };

  const formatPrice = (price: number, currency: string) =>
    new Intl.NumberFormat('vi-VN', { style: 'currency', currency: currency || 'VND' }).format(
      price
    );

  const formatDuration = (ptString: string) => {
    if (!ptString) return '--';
    return ptString.replace('PT', '').replace('H', 'h ').replace('M', 'm').toLowerCase();
  };

  // Tổng hợp tất cả mã chuyến bay để AI phân tích
  const allFlightNumbers = flight.itineraries?.map((it) => it.flightNumber).join(' và ') || '';

  return (
    <div className="group flex w-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:border-blue-300 hover:shadow-md sm:flex-row">
      {/* CỘT TRÁI: CHI TIẾT CHUYẾN BAY */}
      <div className="flex flex-1 flex-col justify-center gap-4 p-5">
        {flight.itineraries?.map((itinerary, index) => (
          <div key={index} className="flex flex-col">
            {/* Hiển thị nhãn Chiều đi / Chiều về nếu là khứ hồi */}
            {flight.itineraries.length > 1 && (
              <span className="mb-2 text-xs font-bold tracking-wider text-slate-400 uppercase">
                {index === 0 ? '✈️ Chiều đi' : '🛬 Chiều về'}
              </span>
            )}

            <div className="flex items-center justify-between">
              {/* Nơi đi */}
              <div className="w-24 text-center">
                <p className="text-2xl font-bold text-slate-800">
                  {formatTime(itinerary.departure.at)}
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-500">
                  {itinerary.departure.iata}
                </p>
              </div>

              {/* Thông tin đường bay */}
              <div className="flex flex-1 flex-col items-center px-4">
                <span className="mb-1 text-xs font-medium text-slate-400">
                  {itinerary.stops === 0 ? 'Bay thẳng' : `${itinerary.stops} điểm dừng`} •{' '}
                  {formatDuration(itinerary.duration)}
                </span>
                <div className="relative flex w-full items-center">
                  <div className="h-[2px] w-full bg-slate-200"></div>
                  <span className="absolute left-1/2 -translate-x-1/2 bg-white px-2 text-slate-300">
                    ✈
                  </span>
                </div>
                <span className="mt-2 rounded bg-blue-50 px-2 py-0.5 text-xs font-semibold tracking-wider text-blue-600 uppercase">
                  {itinerary.flightNumber}
                </span>
              </div>

              {/* Nơi đến */}
              <div className="w-24 text-center">
                <p className="text-2xl font-bold text-slate-800">
                  {formatTime(itinerary.arrival.at)}
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-500">
                  {itinerary.arrival.iata}
                </p>
              </div>
            </div>
          </div>
        ))}

        {/* Thông tin Hành lý (Hiển thị thêm cho chi tiết) */}
        <div className="mt-2 flex flex-wrap gap-2 border-t border-slate-50 pt-2">
          <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
            🎒 Xách tay: {flight.cabinBaggage || 'Không rõ'}
          </span>
          <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
            🧳 Ký gửi: {flight.checkedBaggage || 'Không có'}
          </span>
        </div>
      </div>

      {/* CỘT PHẢI: GIÁ TIỀN & ACTION */}
      <div className="flex flex-col items-center justify-center border-t border-dashed border-slate-200 bg-[#F8FAFC] p-5 sm:w-52 sm:border-t-0 sm:border-l">
        <div className="mb-1 text-center text-xs font-bold tracking-widest text-slate-400 uppercase">
          {flight.cabin || 'Phổ thông'}
          {flight.fareOption && (
            <span className="mt-1 block text-[10px] font-medium text-slate-400 normal-case">
              (Gói: {flight.fareOption})
            </span>
          )}
        </div>
        <p className="text-xl font-extrabold text-[#FF5A5F]">
          {formatPrice(flight.price, flight.currency)}
        </p>

        <button
          onClick={(e) => {
            e.stopPropagation(); // Cực kỳ quan trọng để không click nhầm vào checkbox chọn vé ở ngoài
            onAskAI(
              `Phân tích ưu nhược điểm và hành lý của chuyến bay ${allFlightNumbers} (Hãng: ${
                flight.airlines?.join(', ') || 'N/A'
              }).`
            );
          }}
          className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-xl bg-blue-100 px-4 py-2.5 text-sm font-bold text-blue-700 transition hover:bg-blue-600 hover:text-white"
        >
          ✨ Hỏi AI chuyến này
        </button>
      </div>
    </div>
  );
};

export default FlightOfferCard;
