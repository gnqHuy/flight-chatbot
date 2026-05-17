'use client';

import { useState, useEffect } from 'react';
import { Menu, PanelLeft, SquarePen, MessageSquare, Trash2, Edit } from 'lucide-react';
import { useParams, usePathname, useRouter } from 'next/navigation';
import UserMenu from './UserMenu';
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
    onToggle?.(newState);
  };

  useEffect(() => {
    const handleResize = () => {
      const shouldOpen = window.innerWidth >= 768;
      setIsSidebarOpen(shouldOpen);
      onToggle?.(shouldOpen);
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
  }, [onToggle]);

  const handleNewChat = async () => {
    try {
      setIsLoading(true);

      const newChat = await chatAPI.createConversation('New Chat');

      setConversationList((prev) => [newChat, ...prev]);

      router.push(`/chat/${newChat.id}`);
    } catch (error) {
      console.error('Lỗi khi tạo chat mới:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectChat = (id: string) => {
    if (currentId === id) return;
    router.push(`/chat/${id}`);
  };

  return (
    <aside
      className={`
        m-5 flex flex-col overflow-hidden rounded-2xl bg-white
        transition-[width,box-shadow] duration-300 ease-out
        ${isSidebarOpen ? 'w-80' : 'w-20 items-center shadow-none'}
      `}
    >
      <div
        className={`
          flex items-center p-4
          transition-all duration-300 ease-out
          ${isSidebarOpen ? 'justify-between' : 'justify-center'}
        `}
      >
        <span
          className={`
            overflow-hidden whitespace-nowrap text-lg font-bold tracking-widest text-slate-900 uppercase
            transition-all duration-300 ease-out
            ${isSidebarOpen ? 'max-w-48 translate-x-0 opacity-100' : 'max-w-0 -translate-x-3 opacity-0'}
          `}
        >
          Flight Chatbot
        </span>

        <button
          onClick={toggleSidebar}
          className="rounded-lg p-2 text-slate-500 transition-colors duration-200 hover:bg-slate-100"
          title={isSidebarOpen ? 'Đóng menu' : 'Mở menu'}
        >
          {isSidebarOpen ? <PanelLeft size={20} /> : <Menu size={20} />}
        </button>
      </div>

      <button
        onClick={handleNewChat}
        disabled={isLoading}
        className={`
          m-4 flex items-center gap-3 rounded-lg border border-gray-200 bg-white px-3 py-3
          text-sm font-medium text-gray-700 shadow-sm
          transition-all duration-300 ease-out
          hover:bg-gray-100 hover:text-primary
          disabled:cursor-not-allowed disabled:opacity-70
          ${!isSidebarOpen ? 'h-12 w-12 justify-center px-0' : ''}
        `}
      >
        {isLoading ? (
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        ) : (
          <SquarePen size={20} />
        )}

        <span
          className={`
            overflow-hidden whitespace-nowrap transition-all duration-300 ease-out
            ${isSidebarOpen ? 'max-w-28 translate-x-0 opacity-100' : 'max-w-0 -translate-x-2 opacity-0'}
          `}
        >
          New chat
        </span>
      </button>

      <div className="flex-1 overflow-y-auto overflow-x-hidden">
        {isSidebarOpen ? (
          <div className="animate-[fadeIn_.25s_ease-out]">
            <div className="mx-4 mb-4 flex items-center justify-between border-b border-surface-border pb-3">
              <span className="text-xs font-medium text-slate-500">Your conversations</span>
            </div>

            <div className="scrollbar-thin scrollbar-thumb-slate-200 flex flex-col gap-1 px-3">
              {conversationList.map((conversation) => {
                const isActive = currentId === conversation.id;

                return (
                  <div
                    key={conversation.id}
                    className={`
                      group relative flex w-full items-center justify-between rounded-full p-3 text-sm
                      transition-[background-color,color,border-radius,box-shadow] duration-300 ease-out
                      ${
                        isActive
                          ? 'rounded-r-none bg-primary/5 pr-0 text-primary'
                          : 'bg-transparent text-slate-800 hover:bg-slate-100'
                      }
                    `}
                  >
                    <button
                      onClick={() => handleSelectChat(conversation.id)}
                      className="flex min-w-0 flex-1 items-center gap-3 overflow-hidden text-left"
                      title={conversation.title}
                    >
                      <MessageSquare
                        size={15}
                        className={`
                          shrink-0 transition-colors duration-300
                          ${isActive ? 'text-primary' : 'text-slate-600'}
                        `}
                      />

                      <span
                        className={`
                          truncate transition-all duration-300
                          ${isActive ? 'font-medium' : 'font-normal'}
                        `}
                      >
                        {conversation.title || 'New Conversation'}
                      </span>
                    </button>

                    <div
                      className={`
                        absolute -right-1 z-10 flex h-11 items-center gap-3 rounded-l-full
                        bg-primary/10 p-4 pr-7
                        transition-[opacity,transform] duration-300 ease-out
                        ${
                          isActive
                            ? 'translate-x-0 opacity-100'
                            : 'pointer-events-none translate-x-4 opacity-0'
                        }
                      `}
                    >
                      <button className="text-primary transition-colors hover:text-slate-600">
                        <Trash2 size={15} />
                      </button>

                      <button className="text-primary transition-colors hover:text-slate-600">
                        <Edit size={15} />
                      </button>

                      <svg
                        viewBox="20 0 80 300"
                        className="pointer-events-none absolute -right-2.5 top-1/2 h-28 -translate-y-1/2 overflow-visible"
                      >
                        <g transform="rotate(-90 150 150)">
                          <path
                            d="
                              M0 100
                              C110 100 90 20 150 20
                              C210 20 190 100 300 100
                              L300 100
                              L0 100
                              Z
                            "
                            fill="#f3f4f6"
                          />

                          <circle cx="150" cy="60" r="14" fill="#6366f1" />
                        </g>
                      </svg>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="my-2 w-full border-t border-surface-border" />
        )}
      </div>

      <div className="mx-4 mt-auto border-t border-surface-border py-4">
        <UserMenu collapsed={!isSidebarOpen} />
      </div>
    </aside>
  );
};

export default ChatSidebar;