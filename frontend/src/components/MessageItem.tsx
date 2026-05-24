'use client';

import React from 'react';
import { Role } from '@/types/enums/Role';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User } from 'lucide-react';

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
      
      {/* Avatar */}
      <div 
        className={`relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full shadow-sm ${
          isUser ? 'ml-3 text-black bg-white' : 'mr-3 text-white bg-primary'
        }`}
      >
        {isUser ? <User size={20} strokeWidth={2.5} /> : <Bot size={20} strokeWidth={2.5} />}
      </div>

      <div className={`flex max-w-[85%] sm:max-w-[75%] flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`rounded-2xl px-5 py-3 shadow-sm overflow-hidden ${
            isUser
              ? 'rounded-tr-sm bg-primary text-white'
              : 'rounded-tl-sm border border-surface-border bg-surface-muted text-slate-800'
          }`}
        >
          {isTyping ? (
            <div className="flex items-center gap-1.5 py-1">
              <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]"></span>
              <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]"></span>
              <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400"></span>
            </div>
          ) : (
            <div className={`text-[18px] leading-relaxed ${isUser ? 'text-white' : 'text-slate-800'}`}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ node, ...props }) => <p className="mb-3 last:mb-0" {...props} />,
                  strong: ({ node, ...props }) => <strong className="font-semibold" {...props} />,
                  a: ({ node, ...props }) => (
                    <a
                      target="_blank"
                      rel="noopener noreferrer"
                      className={`break-all underline underline-offset-2 ${isUser ? 'text-blue-200 hover:text-white' : 'text-primary hover:text-primary-hover'}`}
                      {...props}
                    />
                  ),
                  ul: ({ node, ...props }) => <ul className="mb-3 list-outside list-disc pl-5" {...props} />,
                  ol: ({ node, ...props }) => <ol className="mb-3 list-outside list-decimal pl-5" {...props} />,
                  li: ({ node, ...props }) => <li className="mb-1" {...props} />,
                  blockquote: ({ node, ...props }) => (
                    <blockquote
                      className={`my-2 border-l-4 pl-3 italic ${isUser ? 'border-blue-300' : 'border-slate-300 text-slate-600'}`}
                      {...props}
                    />
                  ),
                  
                  // ==========================================
                  // TÙY BIẾN HIỂN THỊ BẢNG (TABLE) CỰC ĐẸP
                  // ==========================================
                  table: ({ node, ...props }) => (
                    <div className={`my-4 w-full overflow-x-auto rounded-xl border shadow-sm ${
                      isUser ? 'border-white/20 bg-white/10' : 'border-slate-200 bg-white'
                    }`}>
                      <table className="w-full text-left text-[18px]" {...props} />
                    </div>
                  ),
                  thead: ({ node, ...props }) => (
                    <thead className={isUser ? 'bg-white/10' : 'bg-slate-50'} {...props} />
                  ),
                  th: ({ node, ...props }) => (
                    <th 
                      className={`border-b px-4 py-3 font-semibold whitespace-nowrap ${
                        isUser ? 'border-white/20 text-white' : 'border-slate-200 text-slate-700'
                      }`} 
                      {...props} 
                    />
                  ),
                  td: ({ node, ...props }) => (
                    <td 
                      className={`border-b px-4 py-3 align-top last:border-b-0 ${
                        isUser ? 'border-white/10' : 'border-slate-100'
                      }`} 
                      {...props} 
                    />
                  ),
                }}
              >
                {text}
              </ReactMarkdown>
            </div>
          )}
        </div>
        {timestamp && (
          <span className="mt-1.5 px-1 text-[14px] font-medium text-slate-400">{timestamp}</span>
        )}
      </div>
    </div>
  );
};

export default MessageItem;