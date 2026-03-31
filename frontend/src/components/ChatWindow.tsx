'use client';

import { chatAPI } from '@/services/chatAPI';
import { ChatMessage } from '@/types/ChatMessage';
import { Role } from '@/types/enums/Role';
import { useState, useRef, useEffect } from 'react';
import MessageItem from './MessageItem';
import ActionRenderer from './ActionRenderer';

type Props = {
  conversationId?: string;
  // Callback để báo cho Layout (Component Cha) biết có Action mới (ví dụ: mở danh sách vé)
  onActionDetected?: (action: any) => void;
  // Hàm này dùng để Component con (như Prompt Chips) có thể ép ChatWindow gửi tin nhắn
  externalInputTrigger?: string;
};

const ChatWindow = ({ conversationId, onActionDetected, externalInputTrigger }: Props) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!conversationId) {
        setMessages([]);
        return;
      }
      try {
        setIsLoadingHistory(true);
        const history = await chatAPI.getHistory(conversationId);
        setMessages(history);

        if (history.length > 0) {
          const latestActionMsg = [...history]
            .reverse()
            .find((msg) => msg.action && msg.action.type === 'flight_list');

          if (latestActionMsg && onActionDetected) {
            onActionDetected(latestActionMsg.action);
          }
        }
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoadingHistory(false);
      }
    };
    fetchHistory();
  }, [conversationId]);

  useEffect(() => {
    if (externalInputTrigger) {
      handleSend(externalInputTrigger);
    }
  }, [externalInputTrigger]);

  // Hàm gửi tin nhắn
  const handleSend = async (messageText?: string) => {
    const textToSend = typeof messageText === 'string' ? messageText : input;
    if (!textToSend.trim() || !conversationId) return;

    const userMsg: ChatMessage = {
      conversation_id: conversationId,
      message_id: Date.now().toString(),
      content: textToSend,
      role: Role.USER,
      intent: '',
      action: null,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsSending(true);

    try {
      const data = await chatAPI.sendMessage(conversationId, textToSend);

      const botMsg: ChatMessage = {
        conversation_id: conversationId,
        message_id: data.message_id || (Date.now() + 1).toString(),
        content: data.content,
        role: data.role || Role.ASSISTANT,
        intent: data.intent || '',
        action: data.action || null,
        created_at: data.created_at || new Date().toISOString(),
      };

      setMessages((prev) => [...prev, botMsg]);

      if (data.action && onActionDetected) {
        onActionDetected(data.action);
      }
    } catch (err) {
      const errorMsg: ChatMessage = {
        conversation_id: conversationId,
        message_id: (Date.now() + 2).toString(),
        content: 'Lỗi kết nối server. Vui lòng thử lại.',
        role: Role.ASSISTANT,
        intent: 'error',
        action: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="mx-auto flex h-full w-full flex-col overflow-hidden bg-white py-4 shadow-sm">
      <div className="scrollbar-thin scrollbar-thumb-gray-200 flex-1 space-y-6 overflow-y-auto px-6">
        {isLoadingHistory ? (
          <div className="flex h-full items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-b-2 border-blue-600"></div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-gray-400">
            <div className="text-center">
              <span className="text-4xl">✈️</span>
              <p className="mt-2 text-sm font-medium">Bắt đầu trò chuyện để tìm vé máy bay</p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.message_id} className="flex w-full flex-col">
              <MessageItem
                role={msg.role}
                text={msg.content}
                timestamp={new Date(msg.created_at).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              />
              <ActionRenderer
                action={msg.action}
                onViewFlightList={(searchId) => {
                  if (onActionDetected) {
                    onActionDetected({
                      type: 'flight_list',
                      payload: { search_id: searchId },
                    });
                  }
                }}
              />
            </div>
          ))
        )}

        {isSending && (
          <div className="flex items-center gap-2 text-sm text-gray-400 italic">
            <div className="h-4 w-4 animate-spin rounded-full border-b-2 border-gray-400"></div>
            AI đang xử lý...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="mt-4 flex gap-2 border-t border-gray-100 px-6 pt-4">
        <input
          className="flex-1 rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-black transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 focus:outline-none disabled:bg-gray-100"
          placeholder={
            conversationId
              ? 'Nhập yêu cầu của bạn (VD: Tìm vé Hà Nội - Đà Lạt ngày mai)'
              : 'Chọn một cuộc hội thoại...'
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          disabled={!conversationId || isLoadingHistory || isSending}
        />

        <button
          onClick={() => handleSend()}
          disabled={!conversationId || isLoadingHistory || isSending || !input.trim()}
          className="rounded-xl bg-blue-600 px-6 py-3 font-medium text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
        >
          Gửi
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
