"use client";
import React, { useState, useRef, useEffect } from "react";
import MessageItem, { type MessageItemProps } from "../MessageItem/MessageItem";
import { sendMessageToBackend } from "../../services/chatAPI";

const ChatWindow = () => {
  const [messages, setMessages] = useState<MessageItemProps[]>([
    {
      id: "1",
      from: "bot",
      text: "Xin chào! Tôi có thể giúp gì cho bạn?",
      timestamp: new Date().toLocaleTimeString(),
    }
  ]);

  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: MessageItemProps = {
      id: Date.now().toString(),
      from: "user",
      text: input,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    const prompt = input;
    setInput("");

    try {
      const data = await sendMessageToBackend(prompt);

      const botMsg: MessageItemProps = {
        id: (Date.now() + 1).toString(),
        from: "bot",
        text: data.intent,
        timestamp: new Date().toLocaleTimeString(),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      const errorMsg: MessageItemProps = {
        id: (Date.now() + 2).toString(),
        from: "bot",
        text: "❌ Không thể kết nối đến server!",
        timestamp: new Date().toLocaleTimeString(),
      };

      setMessages((prev) => [...prev, errorMsg]);
    }
  };

  return (
    <div className="w-full h-screen mx-auto py-4 px-[5%] flex flex-col overflow-hidden bg-white">
      <div className="flex-1 p-4 space-y-4 overflow-y-auto">
        {messages.map((msg) => (
          <MessageItem key={msg.id} {...msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="p-3 flex gap-2">
        <input
          className="flex-1 text-black border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
          placeholder="Nhập tin nhắn..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />

        <button
          onClick={handleSend}
          className="bg-blue-600 px-4 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          Gửi
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
