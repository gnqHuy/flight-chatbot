'use client';

import { FlightOffer } from '@/types/FlightOffer';
import React from 'react';

type Props = {
  flight: FlightOffer;
  onAskAI: (prompt: string) => void;
};

const FlightOfferCard: React.FC<Props> = ({ flight, onAskAI }) => {
  const formatTime = (time: string) =>
    new Date(time).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  const formatPrice = (price: number, currency: string) =>
    new Intl.NumberFormat('vi-VN', { style: 'currency', currency: currency || 'VND' }).format(
      price
    );
  const carrier = flight.flightNumber?.substring(0, 2) || 'FL';

  return (
    <div className="group flex w-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:border-blue-300 hover:shadow-md sm:flex-row">
      <div className="flex flex-1 flex-col justify-between p-5">
        <div className="flex items-center justify-between">
          <div className="w-24 text-center">
            <p className="text-2xl font-bold text-slate-800">{formatTime(flight.departure.at)}</p>
            <p className="mt-1 text-sm font-semibold text-slate-500">{flight.departure.iata}</p>
          </div>
          <div className="flex flex-1 flex-col items-center px-4">
            <span className="mb-1 text-xs font-medium text-slate-400">
              {flight.stops === 0 ? 'Bay thẳng' : `${flight.stops} điểm dừng`} • {flight.duration}
            </span>
            <div className="relative flex w-full items-center">
              <div className="h-[2px] w-full bg-slate-200"></div>
              <span className="absolute left-1/2 -translate-x-1/2 bg-white px-2 text-slate-300">
                ✈
              </span>
            </div>
            <span className="mt-2 rounded bg-blue-50 px-2 py-0.5 text-xs font-semibold tracking-wider text-blue-600 uppercase">
              {flight.flightNumber}
            </span>
          </div>
          s{' '}
          <div className="w-24 text-center">
            <p className="text-2xl font-bold text-slate-800">{formatTime(flight.arrival.at)}</p>
            <p className="mt-1 text-sm font-semibold text-slate-500">{flight.arrival.iata}</p>
          </div>
        </div>
      </div>

      <div className="flex flex-col items-center justify-center border-t border-dashed border-slate-200 bg-[#F8FAFC] p-5 sm:w-52 sm:border-t-0 sm:border-l">
        <p className="mb-1 text-xs font-bold tracking-widest text-slate-400 uppercase">
          {flight.cabin || 'Phổ thông'}
        </p>
        <p className="text-xl font-extrabold text-[#FF5A5F]">
          {formatPrice(flight.price, flight.currency)}
        </p>

        <button
          onClick={() =>
            onAskAI(`Phân tích ưu nhược điểm và hành lý của chuyến bay ${flight.flightNumber}`)
          }
          className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-xl bg-blue-100 px-4 py-2.5 text-sm font-bold text-blue-700 transition hover:bg-blue-600 hover:text-white"
        >
          ✨ Hỏi AI chuyến này
        </button>
      </div>
    </div>
  );
};

export default FlightOfferCard;
