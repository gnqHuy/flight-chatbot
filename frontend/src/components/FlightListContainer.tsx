'use client';

import { useEffect, useState, useMemo } from 'react';
import FlightOfferCard from './FlightOfferCard';
import { FlightOffer } from '@/types/FlightOffer';
import { chatAPI } from '@/services/chatAPI';
import { Heart, Scale, Loader2 } from 'lucide-react';

type Props = {
  conversationId: string;
  searchId: string;
  activeTab: 'VN' | 'VJ' | 'QH';
  onAskAI: (prompt: string) => void;
  onCompareComplete?: (botResponse: any) => void;
};

const FlightListContainer = ({
  conversationId,
  searchId,
  activeTab,
  onAskAI,
  onCompareComplete,
}: Props) => {
  const [allFlights, setAllFlights] = useState<FlightOffer[]>([]);
  const [loading, setLoading] = useState(true);
  const [isComparing, setIsComparing] = useState(false);
  const [isExpired, setIsExpired] = useState(false);
  const [selectedFlights, setSelectedFlights] = useState<string[]>([]);

  useEffect(() => {
    const fetchFlights = async () => {
      if (!searchId) return;
      try {
        setLoading(true);
        setIsExpired(false);
        const data = await chatAPI.getCachedFlights(searchId);
        setAllFlights(data.flights || []);
        setSelectedFlights([]);
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

  const displayedFlights = useMemo(() => {
    if (!allFlights || allFlights.length === 0) return [];

    return allFlights.filter((flight) => {
      if (flight.airlines && flight.airlines.length > 0) {
        return flight.airlines.includes(activeTab);
      }
      const firstItinerary = flight.itineraries?.[0];
      const carrierCode =
        firstItinerary?.flightNumber?.substring(0, 2)?.toUpperCase() ||
        firstItinerary?.segmentDetails?.[0]?.carrierCode;
      return carrierCode === activeTab;
    });
  }, [allFlights, activeTab]);

  const toggleFlightSelection = (flightId: string) => {
    setSelectedFlights((prev) => {
      if (prev.includes(flightId)) {
        return prev.filter((id) => id !== flightId);
      }
      if (prev.length >= 3) {
        alert('Chỉ được chọn tối đa 3 chuyến bay cùng lúc để so sánh!');
        return prev;
      }
      return [...prev, flightId];
    });
  };

  const handleCompare = () => {
    if (selectedFlights.length === 0) return;

    setIsComparing(true);
    
    const flightDetails = selectedFlights.map((id, index) => {
      const flight = allFlights.find((f) => (f.id || (f as any).offerId) === id);
      
      if (flight) {
        const firstItinerary = flight.itineraries?.[0];
        
        const flightNumber = firstItinerary?.flightNumber;
        const carrierCode = firstItinerary?.segmentDetails?.[0]?.carrierCode;
        const displayCode = flightNumber || carrierCode || 'Chuyến bay';
        
        const price = flight.price ? Number(flight.price).toLocaleString('vi-VN') : 'N/A';
        
        return `${index + 1}. Vé ${displayCode} (Giá: $${price}) - Mã hệ thống: ${id}`;
      }
      
      return `- Mã hệ thống: ${id}`;
    });

    const promptMessage = `Hãy phân tích chi tiết và so sánh ưu nhược điểm của các chuyến bay tôi vừa chọn dưới đây:\n\n${flightDetails.join('\n')}`;
    
    onAskAI(promptMessage);

    setSelectedFlights([]);
    setIsComparing(false);
  };

  const handleSave = async () => {
      if (selectedFlights.length === 0) return;
      
      try {
        await Promise.all(selectedFlights.map(async (id) => {
          const flight = allFlights.find((f) => (f.id || (f as any).offerId) === id);
          if (flight) {
            const firstItinerary = flight.itineraries?.[0];
            const flightNumber = firstItinerary?.flightNumber;
            
            if (flightNumber) {
              await chatAPI.saveFlight(conversationId, searchId, flightNumber);
            }
          }
        }));

        alert(`Đã lưu thành công ${selectedFlights.length} vé vào danh sách yêu thích!`);
        setSelectedFlights([]);
        
      } catch (error) {
        console.error('Lỗi khi lưu vé:', error);
        alert('Có lỗi xảy ra khi lưu vé, vui lòng thử lại.');
      }
    };

  if (loading) {
    return (
      <div className="flex h-full flex-col items-center justify-center space-y-4">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
        <p className="animate-pulse text-sm font-medium text-slate-500">
          Đang tải chuyến bay...
        </p>
      </div>
    );
  }

  if (isExpired) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="max-w-md rounded-2xl border border-amber-200 bg-amber-50 p-6 text-center">
          <p className="text-lg font-bold text-amber-800">⏳ Phiên tìm kiếm đã hết hạn</p>
          <p className="mt-2 text-sm text-amber-700">
            Giá vé có thể đã thay đổi. Vui lòng yêu cầu AI tìm kiếm lại.
          </p>
        </div>
      </div>
    );
  }

  if (displayedFlights.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-center">
        <div className="rounded-2xl border border-slate-100 bg-white p-8 shadow-sm">
          <span className="text-4xl">📭</span>
          <p className="mt-4 font-semibold text-slate-700">Không có chuyến bay</p>
          <p className="mt-1 text-sm text-slate-500">
            Hãng bay này không có vé phù hợp với yêu cầu của bạn.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex flex-col gap-2 pb-24">
      {displayedFlights.map((flight, idx) => {
        const flightId = flight.id || `flight-${idx}`;
        const isSelected = selectedFlights.includes(flightId);

        return (
          <div
            key={flightId}
            className={`flex items-center gap-3 rounded-xl border p-2 transition-all duration-200 ${
              isSelected
                ? 'border-blue-400 bg-blue-50 shadow-sm'
                : 'border-transparent bg-transparent hover:bg-slate-50'
            }`}
          >
            <div
              className="flex h-full cursor-pointer items-center justify-center pl-2"
              onClick={() => toggleFlightSelection(flightId)}
            >
              <input
                type="checkbox"
                className="pointer-events-none h-5 w-5 cursor-pointer rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                checked={isSelected}
                readOnly
              />
            </div>

            <div className="w-full flex-1 overflow-hidden">
              <FlightOfferCard flight={flight} onAskAI={onAskAI} />
            </div>
          </div>
        );
      })}

      {selectedFlights.length > 0 && (
        <div className="animate-fade-in-up fixed bottom-4 left-1/2 z-50 flex w-max -translate-x-1/2 items-center gap-4 sm:gap-5 rounded-2xl bg-[#1e293b] px-4 sm:px-5 py-3 shadow-2xl ring-1 ring-white/10">
          
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white shadow-sm">
              {selectedFlights.length}
            </span>
            <span className="whitespace-nowrap text-sm font-medium text-slate-200">
              vé được chọn
            </span>
          </div>

          <div className="h-6 w-px bg-slate-700"></div>

          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              handleSave();
            }}
            className="group flex items-center gap-2 whitespace-nowrap rounded-lg px-2 py-1.5 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-700 hover:text-white"
          >
            <Heart size={18} strokeWidth={2.5} className="transition-transform group-hover:scale-110" />
            <span className="hidden sm:inline">Lưu vé</span>
          </button>

          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              handleCompare();
            }}
            disabled={isComparing}
            className={`flex items-center gap-2 whitespace-nowrap rounded-xl px-5 py-2.5 text-sm font-bold text-white shadow-md transition-all duration-200 ${
              isComparing 
                ? 'cursor-not-allowed bg-slate-600' 
                : 'bg-blue-600 hover:-translate-y-0.5 hover:bg-blue-500 hover:shadow-blue-500/30'
            }`}
          >
            {isComparing ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <Scale size={18} strokeWidth={2.5} />
            )}
            <span>{isComparing ? 'Đang gửi...' : 'Phân tích so sánh'}</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default FlightListContainer;