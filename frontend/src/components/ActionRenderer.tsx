'use client';

import React from 'react';
import { ChatAction } from '@/types/ChatMessage';

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
          <div className="mt-2 ml-12">
            <button
              onClick={() => onViewFlightList?.(flightPayload.search_id)}
              className="group flex w-fit items-center gap-2 rounded-xl border border-blue-200 bg-white px-4 py-2.5 text-sm font-semibold text-blue-600 shadow-sm transition-all hover:border-blue-600 hover:bg-blue-600 hover:text-white hover:shadow-md"
            >
              <span className="text-lg transition-transform group-hover:scale-110">🎫</span>
              Hiển thị danh sách vé
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
