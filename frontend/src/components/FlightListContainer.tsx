'use client';

import { useEffect, useState } from 'react';
import FlightOfferCard from './FlightOfferCard';
import { FlightOffer } from '@/types/FlightOffer'; // Lưu ý: Bạn cần update lại Type này nhé
import { chatAPI } from '@/services/chatAPI';

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

  // CẬP NHẬT THEO CẤU TRÚC MỚI
  const displayedFlights = allFlights.filter((flight) => {
    // Ưu tiên check trong mảng airlines mới được thêm vào
    if (flight.airlines && flight.airlines.length > 0) {
      return flight.airlines.includes(activeTab);
    }
    // Fallback: Lấy carrier code từ chuyến bay của chiều đi (itineraries[0])
    const firstItinerary = flight.itineraries?.[0];
    const carrierCode = firstItinerary?.flightNumber?.substring(0, 2)?.toUpperCase();
    return carrierCode === activeTab;
  });

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
            Không có chuyến bay nào phù hợp với hãng {activeTab}.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex flex-col gap-3 pb-24">
      {displayedFlights.map((flight, idx) => {
        // CẬP NHẬT: Ưu tiên dùng ID của flight, bỏ flightNumber ở root đi
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
            {/* Vùng chỉ dành riêng cho Checkbox */}
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

            {/* Vùng hiển thị Card */}
            <div className="w-full flex-1 overflow-hidden">
              <FlightOfferCard flight={flight} onAskAI={onAskAI} />
            </div>
          </div>
        );
      })}

      {selectedFlights.length > 0 && (
        <div className="animate-fade-in-up fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 items-center gap-4 rounded-full bg-slate-800 px-6 py-3 shadow-xl ring-1 ring-white/10">
          <div className="flex items-center gap-2 border-r border-slate-600 pr-4">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-500 text-xs font-bold text-white">
              {selectedFlights.length}
            </span>
            <span className="text-sm font-medium text-white">vé được chọn</span>
          </div>

          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              handleSave();
            }}
            className="flex items-center gap-1 text-sm font-medium text-slate-200 transition-colors hover:text-white"
          >
            🤍 Lưu vé
          </button>

          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              handleCompare();
            }}
            disabled={isComparing}
            className={`rounded-full px-4 py-2 text-sm font-bold text-white shadow transition-colors ${
              isComparing ? 'cursor-not-allowed bg-slate-500' : 'bg-blue-600 hover:bg-blue-500'
            }`}
          >
            {isComparing ? '⏳ Đang phân tích...' : '⚖️ Phân tích So sánh'}
          </button>
        </div>
      )}
    </div>
  );
};

export default FlightListContainer;
