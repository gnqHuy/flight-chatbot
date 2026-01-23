'use client';

import { chatAPI } from '@/services/chatAPI';
import { ChatMessage } from '@/types/ChatMessage';
import { Role } from '@/types/enums/Role';
import { useState, useRef, useEffect } from 'react';
import MessageItem from './MessageItem';

type Props = {
  conversationId?: string;
};

const ChatWindow = ({ conversationId }: Props) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    fetchHistory();
  }, [conversationId]);

  const handleSend = async () => {
    if (!input.trim() || !conversationId) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      content: input,
      role: 'user',
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    const prompt = input;
    setInput('');

    try {
      const data = await chatAPI.sendMessage(conversationId, prompt);

      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: data.content || data.answer || JSON.stringify(data),
        role: 'assistant',
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 2).toString(),
        content: 'Lỗi kết nối server',
        role: 'assistant',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    }
  };

  return (
    <div className="mx-auto flex h-full w-full flex-col overflow-hidden bg-white px-[5%] py-4">
      <div className="scrollbar-thin scrollbar-thumb-gray-300 flex-1 space-y-4 overflow-y-auto p-4">
        {isLoadingHistory ? (
          <div className="flex h-full items-center justify-center text-gray-400">Loading...</div>
        ) : messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-gray-400">
            Start a conversation
          </div>
        ) : (
          messages.map((msg) => (
            <MessageItem
              key={msg.id}
              role={msg.role === 'user' ? Role.USER : Role.SYSTEM}
              text={msg.content}
              timestamp={new Date(msg.created_at).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}
            />
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2 border-t border-gray-100 p-3">
        <input
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-black focus:ring-2 focus:ring-blue-400 focus:outline-none disabled:bg-gray-100"
          placeholder={conversationId ? 'Type a message...' : 'Select a chat...'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          disabled={!conversationId || isLoadingHistory}
        />

        <button
          onClick={handleSend}
          disabled={!conversationId || isLoadingHistory}
          className="rounded-lg bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700 disabled:bg-gray-400"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
