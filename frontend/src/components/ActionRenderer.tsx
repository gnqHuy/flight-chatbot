'use client';

import React from 'react';
import { ChatAction } from '@/types/ChatMessage';
import { Ticket, ListFilter } from 'lucide-react'; // Bổ sung icon ListFilter

type Props = {
  action: ChatAction | null | undefined;
  onViewFlightList?: (searchId: string) => void;
};

const ActionRenderer: React.FC<Props> = ({ action, onViewFlightList }) => {
  if (!action || !action.type) return null;

  const normalizedType = String(action.type).toLowerCase();
  switch (normalizedType) {
    case 'flight_list':
      const flightPayload = action.payload as any;

      if (flightPayload && flightPayload.search_id) {
        return (
          <div className="ml-12">
            <button
              onClick={() => onViewFlightList?.(flightPayload.search_id)}
              className="group relative flex w-fit items-center gap-2.5 overflow-hidden rounded-xl border border-blue-100 bg-white px-4 py-2.5 text-sm font-semibold text-blue-600 shadow-sm transition-all duration-300 ease-out hover:-translate-y-0.5 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 hover:shadow-md"
            >
              <Ticket 
                size={18} 
                strokeWidth={2.5} 
                className="text-blue-500 transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-110" 
              />
              <span>Hiển thị danh sách vé</span>
              
              <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-blue-100/30 to-transparent transition-transform duration-700 ease-in-out group-hover:translate-x-full" />
            </button>
          </div>
        );
      }
      return null;

    case 'apply_filters':
      const filterPayload = action.payload as any;
      
      if (filterPayload && filterPayload.filtered_id && filterPayload.filtered_id !== 'NONE') {
        return (
          <div className="ml-12">
            <button
              onClick={() => onViewFlightList?.(filterPayload.filtered_id)}
              className="group relative flex w-fit items-center gap-2.5 overflow-hidden rounded-xl border border-indigo-100 bg-white px-4 py-2.5 text-sm font-semibold text-indigo-600 shadow-sm transition-all duration-300 ease-out hover:-translate-y-0.5 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 hover:shadow-md"
            >
              <ListFilter 
                size={18} 
                strokeWidth={2.5} 
                className="text-indigo-500 transition-transform duration-300 group-hover:scale-110" 
              />
              <span>Xem kết quả đã lọc</span>
              
              <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-indigo-100/30 to-transparent transition-transform duration-700 ease-in-out group-hover:translate-x-full" />
            </button>
          </div>
        );
      }
      return null;

    case 'error':
      const errorPayload = action.payload as any;
      if (errorPayload && errorPayload.msg) {
        return (
          <div className="mt-1 ml-12 text-sm font-medium text-red-500">{errorPayload.msg}</div>
        );
      }
      return null;

    default:
      return null;
  }
};

export default ActionRenderer;