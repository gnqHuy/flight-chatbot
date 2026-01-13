"use client";

import React from "react";
import Image from "next/image";

type MessageFrom = "user" | "bot" | "system";

export interface MessageItemProps {
  id?: string;
  from: MessageFrom;
  text: string;
  timestamp?: string;
  isTyping?: boolean;
  className?: string;
  flights?: any[];
}

const MessageItem: React.FC<MessageItemProps> = ({
  id,
  from,
  text,
  timestamp,
  isTyping = false,
  className,
  flights,
}) => {
  const isUser = from === "user";

  return (
    <div
      className={`flex w-full mb-4 ${
        isUser ? "flex-row-reverse" : "flex-row"
      } ${className || ""}`}
    >
      <div className="relative w-8 h-8 flex-shrink-0">
        <Image
          src={isUser ? "/assets/user.svg" : "/assets/chatbot.svg"}
          alt="avatar"
          fill
          className="rounded-full object-cover"
        />
      </div>

      <div className={`flex flex-col max-w-[75%] ${isUser ? "mr-3 items-end" : "ml-3 items-start"}`}>
        <div
          className={`px-4 py-2 rounded-2xl shadow-sm ${
            isUser 
              ? "bg-blue-600 text-white rounded-tr-none" 
              : "bg-white border text-gray-800 rounded-tl-none"
          }`}
        >
          {isTyping ? (
            <div className="flex items-center gap-2 py-1">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></span>
            </div>
          ) : (
            <p className="text-sm whitespace-pre-wrap leading-relaxed">{text}</p>
          )}
        </div>

        {timestamp && (
          <span className="text-[10px] text-gray-400 mt-1 px-1">
            {timestamp}
          </span>
        )}
      </div>
    </div>
  );
};

export default MessageItem;