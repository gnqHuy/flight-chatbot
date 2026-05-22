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
  activeFilters?: Record<string, any>;
  activeSort?: string | null;
};

const FlightListContainer = ({
  conversationId,
  searchId,
  activeTab,
  onAskAI,
  onCompareComplete,
  activeFilters = {},
  activeSort = null,
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

    let result = [...allFlights];

    // 1. Lọc theo Active Tab (Hãng bay)
    result = result.filter((flight) => {
      if (flight.airlines && flight.airlines.length > 0) {
        return flight.airlines.includes(activeTab);
      }
      const firstItinerary = flight.itineraries?.[0];
      const carrierCode =
        firstItinerary?.flightNumber?.substring(0, 2)?.toUpperCase() ||
        firstItinerary?.segmentDetails?.[0]?.carrierCode;
      return carrierCode === activeTab;
    });

    // 2. Lọc theo Active Filters (Giá, Giờ, Bay thẳng, Hạng ghế)
    if (Object.keys(activeFilters).length > 0) {
      result = result.filter((f) => {
        let isMatch = true;

        // 🌟 BỔ SUNG: Lọc Hạng ghế (travelClass)
        if (isMatch && activeFilters.travelClass) {
          if (f.cabin?.toUpperCase() !== activeFilters.travelClass.toUpperCase()) {
            isMatch = false;
          }
        }

        // Lọc giá
        if (isMatch && activeFilters.maxPrice) {
          if (Number(f.price || 0) > Number(activeFilters.maxPrice)) isMatch = false;
        }

        // Lọc bay thẳng
        if (isMatch && activeFilters.nonStop === true) {
          const segmentDetails = f.itineraries?.[0]?.segmentDetails || [];
          // Chú ý: logic cũ của bạn stops < 2 hơi nguy hiểm, nên check đúng length
          if (segmentDetails.length > 1) isMatch = false;
        }

        // Lọc giờ bay
        if (
          isMatch &&
          (activeFilters.start_hour !== undefined || activeFilters.end_hour !== undefined)
        ) {
          const depTimeStr =
            (f as any).departureTime || f.itineraries?.[0]?.segmentDetails?.[0]?.departure?.at;
          if (depTimeStr && depTimeStr.includes('T')) {
            try {
              const hour = parseInt(depTimeStr.split('T')[1].split(':')[0], 10);
              if (activeFilters.start_hour !== undefined && hour < Number(activeFilters.start_hour))
                isMatch = false;
              if (activeFilters.end_hour !== undefined && hour > Number(activeFilters.end_hour))
                isMatch = false;
            } catch (e) {
              console.error('Lỗi parse giờ bay', e);
            }
          }
        }

        return isMatch;
      });
    }

    // 3. Sắp xếp (Active Sort)
    if (activeSort) {
      result.sort((a, b) => {
        const priceA = Number(a.price || 0);
        const priceB = Number(b.price || 0);

        const timeA =
          (a as any).departureTime ||
          a.itineraries?.[0]?.segmentDetails?.[0]?.departure?.at ||
          '9999';
        const timeB =
          (b as any).departureTime ||
          b.itineraries?.[0]?.segmentDetails?.[0]?.departure?.at ||
          '9999';

        switch (activeSort) {
          case 'price_desc':
            return priceB - priceA; // Giá đắt nhất lên đầu
          case 'price_asc':
            return priceA - priceB; // Giá rẻ nhất lên đầu
          case 'departure_time':
            return timeA.localeCompare(timeB);
          case 'arrival_time':
            const arrA =
              (a as any).arrivalTime ||
              a.itineraries?.[0]?.segmentDetails?.[a.itineraries[0].segmentDetails.length - 1]
                ?.arrival?.at ||
              '9999';
            const arrB =
              (b as any).arrivalTime ||
              b.itineraries?.[0]?.segmentDetails?.[b.itineraries[0].segmentDetails.length - 1]
                ?.arrival?.at ||
              '9999';
            return arrA.localeCompare(arrB);
          default:
            return 0;
        }
      });
    } else {
      // Mặc định luôn sắp xếp giá tăng dần nếu không có lệnh gì
      result.sort((a, b) => Number(a.price || 0) - Number(b.price || 0));
    }

    return result;
  }, [allFlights, activeTab, activeFilters, activeSort]);

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

  const handleCompare = async () => {
    if (selectedFlights.length === 0) return;

    if (!conversationId) {
      alert('Lỗi hệ thống: Không tìm thấy ID phiên chat để tiếp tục!');
      return;
    }

    setIsComparing(true);

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/conversations/${conversationId}/resume`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            selected_flight_ids: selectedFlights,
          }),
        }
      );

      if (!response.ok) throw new Error('Lỗi gọi API Resume');

      const data = await response.json();

      if (onCompareComplete) {
        onCompareComplete(data);
      }

      setSelectedFlights([]);
    } catch (error) {
      console.error('Lỗi khi resume phân tích:', error);
      alert('Có lỗi xảy ra khi phân tích vé. Vui lòng thử lại.');
    } finally {
      setIsComparing(false);
    }
  };

  const handleSave = () => {
    if (selectedFlights.length === 0) return;
    alert(`Đã lưu ${selectedFlights.length} vé vào danh sách yêu thích!`);
    setSelectedFlights([]);
  };

  if (loading) {
    return (
      <div className="flex h-full flex-col items-center justify-center space-y-4">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
        <p className="animate-pulse text-sm font-medium text-slate-500">
          Đang tìm chuyến bay tốt nhất...
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
          <p className="mt-4 font-semibold text-slate-700">Không tìm thấy chuyến bay</p>
          <p className="mt-1 text-sm text-slate-500">
            Không có chuyến bay nào phù hợp với bộ lọc hiện tại.
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
          
          {/* 1. Phần số lượng vé */}
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white shadow-sm">
              {selectedFlights.length}
            </span>
            <span className="whitespace-nowrap text-sm font-medium text-slate-200">
              vé được chọn
            </span>
          </div>

          {/* Đường vạch chia cách */}
          <div className="h-6 w-px bg-slate-700"></div>

          {/* 2. Nút Lưu vé */}
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

          {/* 3. Nút Phân tích So sánh */}
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
            <span>{isComparing ? 'Đang phân tích...' : 'Phân tích so sánh'}</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default FlightListContainer;
