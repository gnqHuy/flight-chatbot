'use client';

import { useState, useEffect } from 'react';
import { Menu, PanelLeft, SquarePen, MessageSquare } from 'lucide-react';
import { useParams, usePathname, useRouter } from 'next/navigation';
import UserMenu from './UserMenu';
import api from '@/utils/api';
import { Conversation } from '@/types/Conversation';
import { chatAPI } from '@/services/chatAPI';

type Props = {
  onToggle?: (isOpen: boolean) => void;
};

const ChatSidebar = ({ onToggle }: Props) => {
  const pathname = usePathname();
  if (pathname === '/login') return null;

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationList, setConversationList] = useState<Conversation[]>([]);
  const router = useRouter();
  const params = useParams();
  const currentId = params?.id;

  const toggleSidebar = () => {
    const newState = !isSidebarOpen;
    setIsSidebarOpen(newState);
    if (onToggle) onToggle(newState);
  };

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setIsSidebarOpen(false);
      } else {
        setIsSidebarOpen(true);
      }
    };

    const handleGetConversations = async () => {
      try {
        setIsLoading(true);
        const data = await chatAPI.getConversations();

        const sortedList = data.sort((a: any, b: any) => {
          const timeA = new Date(a.updated_at || a.created_at).getTime();
          const timeB = new Date(b.updated_at || b.created_at).getTime();

          return timeB - timeA;
        });

        setConversationList(sortedList);
      } catch (error) {
        console.error('Lỗi khi lấy danh sách cuộc trò chuyện:', error);
      } finally {
        setIsLoading(false);
      }
    };

    handleResize();
    if (typeof window !== 'undefined' && localStorage.getItem('accessToken')) {
      handleGetConversations();
    }

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleNewChat = async () => {
    try {
      setIsLoading(true);
      const newChat = await chatAPI.createConversation('New Chat');
      router.push(`/chat/${newChat.id}`);
    } catch (error) {
      console.error('Lỗi khi tạo chat mới:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectChat = (id: string) => {
    router.push(`/chat/${id}`);
  };

  return (
    <div
      className={`relative flex h-full flex-col border-r border-gray-200 bg-gray-50 transition-all duration-300 ease-in-out ${isSidebarOpen ? 'w-72 p-4' : 'w-20 items-center p-4'} `}
    >
      <div
        className={`mb-6 flex flex-row items-center ${isSidebarOpen ? 'justify-between' : 'justify-center'}`}
      >
        {isSidebarOpen && (
          <span className="truncate text-lg font-bold text-gray-700">FlightBot</span>
        )}

        <button
          onClick={toggleSidebar}
          className="rounded-md p-2 text-gray-500 transition-colors hover:bg-gray-200"
          title={isSidebarOpen ? 'Đóng menu' : 'Mở menu'}
        >
          {isSidebarOpen ? <PanelLeft size={20} /> : <Menu size={20} />}
        </button>
      </div>

      <button
        onClick={handleNewChat}
        disabled={isLoading}
        className={`mb-4 flex items-center gap-3 rounded-lg border border-gray-200 bg-white px-3 py-3 text-sm font-medium text-gray-700 shadow-sm transition-all hover:bg-gray-100 hover:text-blue-600 ${!isSidebarOpen && 'h-12 w-12 justify-center px-0'} `}
      >
        {isLoading ? (
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
        ) : (
          <SquarePen size={20} />
        )}

        <div
          className={`overflow-hidden transition-all duration-200 ${isSidebarOpen ? 'w-auto opacity-100' : 'hidden'}`}
        >
          <span className="whitespace-nowrap">New chat</span>
        </div>
      </button>

      <div className="flex-1 overflow-y-auto">
        {isSidebarOpen ? (
          <>
            <div className="px-2 py-2 text-xs font-medium text-gray-400">Gần đây</div>
            <div className="flex flex-col gap-1">
              {conversationList.map((conversation) => {
                const isActive = currentId === conversation.id;

                return (
                  <button
                    key={conversation.id}
                    onClick={() => handleSelectChat(conversation.id)}
                    className={`group flex w-full items-center gap-3 rounded-md border px-3 py-2 text-sm font-medium transition-all ${
                      isActive
                        ? 'border-blue-200 bg-blue-100 text-blue-700'
                        : 'border-transparent bg-transparent text-gray-700 hover:bg-gray-200 hover:text-gray-900'
                    } `}
                    title={conversation.title}
                  >
                    <span className={`truncate ${isActive ? 'font-semibold' : ''}`}>
                      {conversation.title || 'Đoạn chat không tên'}
                    </span>
                  </button>
                );
              })}
            </div>
          </>
        ) : (
          <div className="my-2 w-full border-t border-gray-200"></div>
        )}
      </div>

      <div className="mt-auto">
        <UserMenu collapsed={!isSidebarOpen} />
      </div>
    </div>
  );
};

export default ChatSidebar;
