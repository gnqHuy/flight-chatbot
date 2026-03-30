'use client';

import { useEffect, useState } from 'react';
import FlightOfferCard from './FlightOfferCard';
import { FlightOffer } from '@/types/FlightOffer'; // Adjust type import if needed
import { chatAPI } from '@/services/chatAPI';

type Props = {
  searchId: string;
  activeTab: 'ALL' | 'VN' | 'VJ' | 'QH';
  onAskAI: (prompt: string) => void;
};

const FlightListContainer = ({ searchId, activeTab, onAskAI }: Props) => {
  const [allFlights, setAllFlights] = useState<FlightOffer[]>([]);
  const [loading, setLoading] = useState(true);
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    const fetchFlights = async () => {
      if (!searchId) return;
      try {
        setLoading(true);
        setIsExpired(false);
        const data = await chatAPI.getCachedFlights(searchId);
        setAllFlights(data.flights || []);
      } catch (error: any) {
        if (error.response?.status === 410) {
          setIsExpired(true);
        } else {
          console.error('Lỗi lấy vé:', error);
        }
      } finally {
        setLoading(false);
      }
    };
    fetchFlights();
  }, [searchId]);

  // Logic lọc theo tab hãng bay
  const displayedFlights = allFlights.filter((flight) => {
    if (activeTab === 'ALL') return true;
    
    // Giả định flight có trường flightNumber (vd: VN208) hoặc validatingAirlineCodes
    const carrierCode = flight.flightNumber?.substring(0, 2)?.toUpperCase();
    return carrierCode === activeTab;
  });

  if (loading) {
    return (
      <div className="flex h-full flex-col items-center justify-center space-y-4">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
        <p className="text-sm font-medium text-slate-500 animate-pulse">Đang tìm chuyến bay tốt nhất...</p>
      </div>
    );
  }

  if (isExpired) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="max-w-md rounded-2xl border border-amber-200 bg-amber-50 p-6 text-center">
          <p className="text-lg font-bold text-amber-800">⏳ Phiên tìm kiếm đã hết hạn</p>
          <p className="mt-2 text-sm text-amber-700">Giá vé có thể đã thay đổi. Vui lòng yêu cầu AI tìm kiếm lại.</p>
        </div>
      </div>
    );
  }

  if (displayedFlights.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-center">
        <div className="rounded-2xl bg-white p-8 shadow-sm border border-slate-100">
          <span className="text-4xl">📭</span>
          <p className="mt-4 font-semibold text-slate-700">Không tìm thấy chuyến bay</p>
          <p className="text-sm text-slate-500 mt-1">Không có chuyến bay nào phù hợp với hãng {activeTab !== 'ALL' ? activeTab : 'này'}.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 pb-8">
      {displayedFlights.map((flight, idx) => (
        <FlightOfferCard
          key={flight.id || idx}
          flight={flight}
          onAskAI={onAskAI}
        />
      ))}
    </div>
  );
};

export default FlightListContainer;