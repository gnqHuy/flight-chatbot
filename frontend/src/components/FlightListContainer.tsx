'use client';

import { useEffect, useState } from 'react';
import FlightOfferCard from './FlightOfferCard';
import { FlightOffer } from '@/types/ChatMessage';
import { chatAPI } from '@/services/chatAPI';

type Props = {
  searchId: string;
};

const FlightListContainer = ({ searchId }: Props) => {
  const [flights, setFlights] = useState<FlightOffer[]>([]);
  const [loading, setLoading] = useState(true);
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    const fetchFlights = async () => {
      if (!searchId) return;

      try {
        setLoading(true);
        const data = await chatAPI.getCachedFlights(searchId);
        setFlights(data.flights || []);
      } catch (error: any) {
        if (error.response && error.response.status === 410) {
          setIsExpired(true);
        } else {
          console.error('Lỗi lấy vé từ cache:', error);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchFlights();
  }, [searchId]);

  return (
    <>
      {loading ? (
        <div className="mt-2 pr-4 pl-12 text-sm text-gray-500 italic">
          Đang tải thông tin chuyến bay...
        </div>
      ) : isExpired ? (
        <div className="mt-2 ml-12 w-full max-w-[70%] rounded-lg border border-gray-300 bg-gray-50 p-4 text-center">
          <p className="font-medium text-gray-600">Phiên tìm kiếm vé này đã hết hạn.</p>
          <p className="text-sm text-gray-500">
            Giá vé có thể đã thay đổi. Vui lòng nhắn tin để bot tìm lại nhé!
          </p>
        </div>
      ) : (
        <div className="mt-2 ml-12 flex flex-col gap-3">
          {flights.map((flight) => (
            <FlightOfferCard
              key={flight.id}
              flight={flight}
              onSelectFlight={(selected) => {
                console.log('User vừa chọn vé: ', selected);
              }}
            />
          ))}
        </div>
      )}
    </>
  );
};

export default FlightListContainer;
