'use client';

import { useState } from 'react';
import ChatWindow from './ChatWindow';
import FlightListContainer from './FlightListContainer';
import { X, Ticket, Heart } from 'lucide-react'; // Bổ sung import icon
import SavedFlightsPanel from './SavedFlightsPanel';


type Props = {
  conversationId: string;
};

export default function ChatLayout({ conversationId }: Props) {
  const [isWorkspaceOpen, setIsWorkspaceOpen] = useState(false);
  const [currentSearchId, setCurrentSearchId] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<'VN' | 'VJ' | 'QH'>('VN');
  const [externalTrigger, setExternalTrigger] = useState<string>('');

  const [isCartOpen, setIsCartOpen] = useState(false);

  const handleActionDetected = (action: any) => {
    if (!action) return;

    if (action.type === 'flight_list' || action.type === 'FLIGHT_LIST') {
      if (action.payload?.search_id) {
        setCurrentSearchId(action.payload.search_id);
        setIsWorkspaceOpen(true);
      }
    }

    if (action.type === 'apply_filters' || action.type === 'APPLY_FILTERS') {
      const { search_id, filtered_id } = action.payload || {};
      if (filtered_id && filtered_id !== 'NONE') {
        setCurrentSearchId(filtered_id);
      } else if (search_id) {
        setCurrentSearchId(search_id);
      }
      
      setIsWorkspaceOpen(true);
    }
  };

  const handlePromptClick = (promptText: string) => {
    setExternalTrigger(`${promptText} `);
  };

  const handleCompareComplete = (botResponse: any) => {
    console.log('Đã so sánh xong, response từ Backend:', botResponse);
  };

  return (
    <div className="flex bg-gray-100 h-screen w-full overflow-hidden text-gray-800 relative">
      
      {/* NÚT MỞ (Chỉ hiện khi Workspace đang đóng và đã có vé) */}
      {/* {!isWorkspaceOpen && currentSearchId && (
        <button
          onClick={() => setIsWorkspaceOpen(true)}
          className="absolute top-[50%] right- -translate-y-1/2 -rotate-90 z-20 flex items-center gap-2 rounded-full bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg transition-all hover:-translate-x-0.5 hover:bg-blue-500 hover:shadow-blue-500/30 animate-in fade-in zoom-in duration-300"
        >
          <Ticket size={18} />
          <span>Xem danh sách vé</span>
        </button>
      )} */}

      <div className={`absolute top-5 z-20 flex items-center gap-3${
          isWorkspaceOpen ? ' right-20' : ' right-6'
        }`}>
        {/* NÚT MỞ GIỎ HÀNG (LUÔN HIỆN) */}
        <button
          onClick={() => setIsCartOpen(true)}
          title="Xem vé đã lưu"
          className="flex h-10 w-10 items-center justify-center rounded-full bg-white text-rose-500 shadow-md transition-all hover:-translate-y-0.5 hover:bg-rose-50 hover:shadow-lg"
        >
          <Heart size={20} strokeWidth={2.5} />
        </button>
      </div>

      {/* KHUNG CHAT (Bên trái) */}
      <div
        className={`relative h-full transition-all duration-500 ease-in-out ${
          isWorkspaceOpen ? 'z-10 w-[50%] border-r border-surface-border shadow-lg' : 'mx-auto w-full'
        }`}
      >
        <ChatWindow
          isWorkspaceOpen={isWorkspaceOpen}
          conversationId={conversationId}
          onActionDetected={handleActionDetected}
          externalInputTrigger={externalTrigger}
        />
      </div>

      {/* KHUNG WORKSPACE - DANH SÁCH VÉ (Bên phải) */}
      <div
        className={`flex h-full flex-col bg-surface-muted transition-all duration-500 ease-in-out ${
          isWorkspaceOpen
            ? 'w-[50%] translate-x-0 opacity-100'
            : 'w-0 translate-x-full overflow-hidden opacity-0'
        }`}
      >
        {isWorkspaceOpen && currentSearchId && (
          <div className="animate-in fade-in flex h-full w-full flex-col p-6 duration-500">
            
            {/* Header & Nút Đóng (X) */}
            <div className="mb-2 shrink-0">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-2xl font-bold tracking-tight text-slate-800">
                  Danh sách chuyến bay
                </h2>
                
                {/* NÚT ĐÓNG (X) */}
                <button
                  onClick={() => setIsWorkspaceOpen(false)}
                  className="rounded-full bg-slate-200 p-2 text-slate-500 transition-colors hover:bg-slate-300 hover:text-slate-800"
                  title="Đóng danh sách vé"
                >
                  <X size={20} strokeWidth={2.5} />
                </button>
              </div>

              {/* Tabs Hãng Bay */}
              <div className="flex space-x-1 border-b border-surface-border">
                {[
                  { id: 'VN', label: 'Vietnam Airlines' },
                  { id: 'VJ', label: 'Vietjet Air' },
                  { id: 'QH', label: 'Bamboo Airways' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`rounded-t-xl px-5 py-2.5 text-sm font-semibold transition-all ${
                      activeTab === tab.id
                        ? 'border-b-2 border-primary bg-white text-primary shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]'
                        : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="scrollbar-thin scrollbar-thumb-gray-300 flex-1 overflow-y-auto pr-2">
              <FlightListContainer
                conversationId={conversationId}
                searchId={currentSearchId}
                activeTab={activeTab}
                onAskAI={handlePromptClick}
                onCompareComplete={handleCompareComplete}
              />
            </div>
          </div>
        )}
      </div>

      <SavedFlightsPanel
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
        conversationId={conversationId}
        onAskAI={handlePromptClick}
      />
    </div>
  );
}