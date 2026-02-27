'use client';

import React from 'react';
import { ChatAction } from '@/types/ChatMessage';
import { ComponentType } from '@/types/enums/ComponentType';
import FlightListContainer from './FlightListContainer';

type Props = {
  action: ChatAction | null | undefined;
};

const ActionRenderer: React.FC<Props> = ({ action }) => {
  if (!action) return null;

  switch (action.type) {
    case ComponentType.FLIGHT_LIST:
    case 'flight_list':
      if (action.payload && 'search_id' in action.payload) {
        return <FlightListContainer searchId={action.payload.search_id} />;
      }
      return null;

    case ComponentType.ERROR:
    case 'error':
      if (action.payload && 'msg' in action.payload) {
        return <div className="mt-2 pl-12 text-red-500">{action.payload.msg}</div>;
      }
      return null;

    default:
      return null;
  }
};

export default ActionRenderer;
