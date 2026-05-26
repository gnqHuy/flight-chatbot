'use client';

import { useEffect, useState } from 'react';
import { X, Heart, Loader2 } from 'lucide-react';
import { FlightOffer } from '@/types/FlightOffer';
import { chatAPI } from '@/services/chatAPI';
import FlightOfferCard from './FlightOfferCard';

type Props = {
  isOpen: boolean;
  onClose: () => void;
  conversationId: string;
  onAskAI: (prompt: string) => void;
};

export default function SavedFlightsPanel({ isOpen, onClose, conversationId, onAskAI }: Props) {
  const [flights, setFlights] = useState<FlightOffer[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen && conversationId) {
      const fetchSavedFlights = async () => {
        setIsLoading(true);
        try {
          const data = await chatAPI.getSavedFlights(conversationId);
          setFlights(data.flights || []);
        } catch (error) {
          console.error('Lỗi khi lấy giỏ hàng:', error);
        } finally {
          setIsLoading(false);
        }
      };
      fetchSavedFlights();
    }
  }, [isOpen, conversationId]);

  if (!isOpen) return null;

  return (
    <div className="absolute inset-0 z-50 flex justify-end bg-slate-900/20 backdrop-blur-sm transition-all duration-300">
      {/* Nền bấm để đóng */}
      <div className="absolute inset-0 cursor-pointer" onClick={onClose} />

      {/* Panel nội dung */}
      <div className="relative flex h-full w-full max-w-xl flex-col bg-surface-muted shadow-2xl animate-in slide-in-from-right-full duration-300">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
          <div className="flex items-center gap-2 text-rose-500">
            <Heart size={22} className="fill-rose-500" />
            <h2 className="text-xl font-bold text-slate-800">Vé đã lưu</h2>
            <span className="ml-2 rounded-full bg-rose-100 px-2.5 py-0.5 text-sm font-bold text-rose-600">
              {flights.length}
            </span>
          </div>
          <button
            onClick={onClose}
            className="rounded-full bg-slate-100 p-2 text-slate-500 transition hover:bg-slate-200 hover:text-slate-800"
          >
            <X size={20} />
          </button>
        </div>

        {/* Nội dung danh sách */}
        <div className="scrollbar-hide flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex h-full flex-col items-center justify-center text-slate-500">
              <Loader2 size={32} className="mb-4 animate-spin text-rose-400" />
              <p>Đang tải giỏ hàng...</p>
            </div>
          ) : flights.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <Heart size={48} className="mb-4 text-slate-200" />
              <p className="font-medium text-slate-600">Chưa có chuyến bay nào được lưu.</p>
              <p className="mt-1 text-sm text-slate-400">Bạn có thể chọn và lưu các chuyến bay ưng ý từ danh sách tìm kiếm.</p>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {flights.map((flight, idx) => (
                <div key={flight.id || idx} className="relative">
                  <FlightOfferCard 
                    flight={flight} 
                    onAskAI={(prompt) => {
                      onAskAI(prompt);
                      onClose(); // Đóng giỏ hàng khi user bấm hỏi AI
                    }} 
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}