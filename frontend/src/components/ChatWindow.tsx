'use client';

import { chatAPI } from '@/services/chatAPI';
import { ChatMessage } from '@/types/ChatMessage';
import { Role } from '@/types/enums/Role';
import { useState, useRef, useEffect } from 'react';
import MessageItem from './MessageItem';
import ActionRenderer from './ActionRenderer';
import { ArrowRight, Sparkles } from 'lucide-react';

type Props = {
  conversationId?: string;
  onActionDetected?: (action: any) => void;
  externalInputTrigger?: string;
};

const suggestions = [
  'Tìm vé máy bay từ Hà Nội đi Đà Nẵng vào ngày mai',
  'Chính sách hoàn hủy vé',
  'Khuyến mãi vé máy bay tháng này',
];

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

        const latestActionMsg = [...history]
          .reverse()
          .find((msg) => msg.action && ['flight_list', 'apply_filters'].includes(msg.action.type));

        if (latestActionMsg && onActionDetected) {
          onActionDetected(latestActionMsg.action);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    fetchHistory();
  }, [conversationId, onActionDetected]);

  useEffect(() => {
    if (externalInputTrigger) {
      handleSend(externalInputTrigger);
    }
  }, [externalInputTrigger]);

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
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          conversation_id: conversationId,
          message_id: (Date.now() + 2).toString(),
          content: 'Lỗi kết nối server. Vui lòng thử lại.',
          role: Role.ASSISTANT,
          intent: 'error',
          action: null,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const isEmptyState = !conversationId || messages.length === 0;

  return (
    <div className="relative mx-auto flex h-full w-full flex-col overflow-hidden bg-transparent">
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[70%] bg-[radial-gradient(circle_at_45%_85%,rgba(244,114,182,0.22),transparent_55%),radial-gradient(circle_at_60%_80%,rgba(99,102,241,0.18),transparent_60%)]" />
      <div className="relative flex-1 overflow-hidden">
        {isLoadingHistory ? (
          <div className="flex h-full items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-primary" />
          </div>
        ) : isEmptyState ? (
          <div className="flex h-full flex-col items-center justify-center px-6">
            <Sparkles size={34} className="mb-8 text-slate-900" />
            <h2 className="text-2xl font-medium text-slate-900">Ask our Chatbot something</h2>
          </div>
        ) : (
          <div className="scrollbar-thin scrollbar-thumb-gray-200 h-full space-y-6 overflow-y-auto px-6 py-6">
            {messages.map((msg) => (
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
                  onViewFlightList={() => {
                    if (msg.action) {
                      onActionDetected?.(msg.action);
                    }
                  }}
                />
              </div>
            ))}

            {isSending && (
              <div className="flex items-center gap-2 text-[13px] text-slate-400 italic">
                <div className="h-4 w-4 animate-spin rounded-full border-b-2 border-slate-400" />
                AI đang xử lý...
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="relative z-10 px-6 pb-8">
        {isEmptyState && (
          <div className="mx-auto mb-7 w-full max-w-4xl">
            <p className="mb-3 text-sm font-medium text-slate-700">
              Suggestions on what to ask Chatbot
            </p>

            <div className="flex flex-wrap gap-3">
              {suggestions.map((item) => (
                <button
                  key={item}
                  onClick={() => setInput(item)}
                  className="
                    rounded-xl
                    border border-white/70
                    bg-white/60
                    px-4 py-3
                    text-left text-sm text-slate-900
                    shadow-sm
                    backdrop-blur
                    transition-all
                    hover:bg-white
                    hover:shadow-md
                  "
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="mx-auto flex w-full max-w-4xl items-center rounded-lg border border-slate-300 bg-white">
          <input
            className="flex-1 bg-transparent px-4 py-4 text-sm text-slate-800 outline-none disabled:cursor-not-allowed disabled:opacity-60"
            placeholder={
              conversationId
                ? 'Ask me anything about your journey...'
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
            className="mr-3 flex h-10 w-10 shrink-0 items-center justify-center text-slate-400 transition hover:text-primary disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ArrowRight size={28} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;