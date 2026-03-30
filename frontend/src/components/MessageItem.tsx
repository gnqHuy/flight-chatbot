'use client';

import React from 'react';
import Image from 'next/image';
import { Role } from '@/types/enums/Role';

export interface MessageItemProps {
  role: Role;
  text: string;
  timestamp?: string;
  isTyping?: boolean;
}

const MessageItem: React.FC<MessageItemProps> = ({ role, text, timestamp, isTyping }) => {
  const isUser = String(role).toLowerCase() === 'user';

  return (
    <div className={`mb-5 flex w-full ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <div className={`relative h-9 w-9 flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
        <Image
          src={isUser ? '/assets/user.svg' : '/assets/chatbot.svg'}
          alt={isUser ? 'User' : 'Bot'}
          fill
          className="rounded-full border border-slate-100 object-cover shadow-sm"
        />
      </div>

      <div className={`flex max-w-[75%] flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`rounded-2xl px-5 py-3 shadow-sm ${
            isUser
              ? 'rounded-tr-sm bg-blue-600 text-white'
              : 'rounded-tl-sm border border-slate-200 bg-[#F1F5F9] text-slate-800'
          }`}
        >
          {isTyping ? (
            <div className="flex items-center gap-1.5 py-1">
              <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]"></span>
              <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]"></span>
              <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400"></span>
            </div>
          ) : (
            <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{text}</p>
          )}
        </div>
        {timestamp && (
          <span className="mt-1.5 px-1 text-[11px] font-medium text-slate-400">{timestamp}</span>
        )}
      </div>
    </div>
  );
};

export default MessageItem;
