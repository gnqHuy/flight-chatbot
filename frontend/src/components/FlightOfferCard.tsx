'use client';

import { FlightOffer } from '@/types/FlightOffer';
import React from 'react';

type Props = {
  flight: FlightOffer;
  onSelectFlight?: (flight: FlightOffer) => void;
};

const FlightOfferCard: React.FC<Props> = ({ flight, onSelectFlight }) => {
  const formatDate = (time: string): string => {
    const date = new Date(time);
    return date.toLocaleString('en-GB', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    });
  };

  const formatTime = (time: string): string => {
    const date = new Date(time);
    return date.toLocaleString([], {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: currency || 'VND',
    }).format(price);
  };

  return (
    <div className="mb-4 flex w-[70%] overflow-hidden rounded-lg border bg-white shadow-md transition-shadow hover:shadow-lg">
      <div className="flex-1 p-4">
        <div className="flex items-center justify-between">
          <div className="text-left">
            <div className="small:text-xl text-2xl font-semibold text-gray-900">
              {formatTime(flight.departure.at)}
            </div>
            <div className="text-sm font-normal text-gray-500">
              {formatDate(flight.departure.at)}
            </div>
            <div className="mt-1 text-lg font-medium text-yellow-600">
              {flight.departure.city} ({flight.departure.iata})
            </div>
          </div>

          <div className="flex flex-col items-center text-yellow-600">
            <div className="mb-1 text-xs text-gray-500">
              {flight.stops === 0 ? 'Bay thẳng' : `${flight.stops} điểm dừng`}
            </div>
            <div className="flex items-center">
              <div className="h-0.5 w-20 bg-gray-300"></div>
              <svg
                className="mx-2 h-5 w-5 rotate-90 transform"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" />
              </svg>
              <div className="h-0.5 w-20 bg-gray-300"></div>
            </div>
          </div>

          <div className="text-right">
            <div className="small:text-xl text-2xl font-semibold text-gray-900">
              {formatTime(flight.arrival.at)}
            </div>
            <div className="text-sm font-normal text-gray-500">{formatDate(flight.arrival.at)}</div>
            <div className="mt-1 text-lg font-medium text-yellow-600">
              {flight.arrival.city} ({flight.arrival.iata})
            </div>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between text-sm text-gray-700">
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <svg
                className="mr-2 h-4 w-4 text-yellow-600"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span className="font-semibold">{flight.duration}</span>
            </div>
            <div className="flex items-center">
              <svg
                className="mr-1 h-5 w-5 text-yellow-600"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
              <span>{flight.baggage}</span>
            </div>
          </div>
          <div>
            <span className="font-medium">{flight.flightNumber}</span>
          </div>
        </div>
      </div>

      <div className="flex w-[30%] flex-col items-center justify-center border-l border-gray-200 bg-gray-50 p-4">
        <div className="mb-2 text-sm font-semibold tracking-wider text-gray-500 uppercase">
          {flight.cabin}
        </div>
        <div className="mb-4 text-center text-2xl font-bold text-emerald-600">
          {formatPrice(flight.price, flight.currency)}
        </div>
        <button
          onClick={() => onSelectFlight?.(flight)}
          className="w-full rounded bg-yellow-500 px-4 py-2 font-semibold text-white transition-colors hover:bg-yellow-600"
        >
          Chọn vé này
        </button>
      </div>
    </div>
  );
};

export default FlightOfferCard;
