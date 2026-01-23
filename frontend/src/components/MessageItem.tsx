'use client';

import React from 'react';
import Image from 'next/image';
import { Role } from '@/types/enums/Role';

export interface MessageItemProps {
  id?: string;
  role: Role;
  text: string;
  timestamp?: string;
  isTyping?: boolean;
  className?: string;
  flights?: any[];
}

const MessageItem: React.FC<MessageItemProps> = ({
  id,
  role,
  text,
  timestamp,
  isTyping = false,
  className,
  flights,
}) => {
  const isUser = role === Role.USER;

  return (
    <div
      className={`mb-4 flex w-full ${isUser ? 'flex-row-reverse' : 'flex-row'} ${className || ''}`}
    >
      <div className="relative h-8 w-8 flex-shrink-0">
        <Image
          src={isUser ? '/assets/user.svg' : '/assets/chatbot.svg'}
          alt={isUser ? 'User Avatar' : 'Bot Avatar'}
          fill
          className="rounded-full object-cover"
        />
      </div>

      <div
        className={`flex max-w-[65%] flex-col ${isUser ? 'mr-3 items-end' : 'ml-3 items-start'}`}
      >
        <div
          className={`rounded-2xl px-4 py-2 shadow-sm ${
            isUser
              ? 'rounded-tr-none bg-blue-600 text-white'
              : 'rounded-tl-none bg-gray-100 text-gray-800'
          }`}
        >
          {isTyping ? (
            <div className="flex items-center gap-2 py-1">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.3s]"></span>
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.15s]"></span>
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400"></span>
            </div>
          ) : (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{text}</p>
          )}
        </div>

        {timestamp && <span className="mt-1 px-1 text-[12px] text-gray-400">{timestamp}</span>}
      </div>
    </div>
  );
};

export default MessageItem;
