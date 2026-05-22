'use client';

import { useState } from 'react';
import ChatWindow from './ChatWindow';
import FlightListContainer from './FlightListContainer';

type Props = {
  conversationId: string;
};

export default function ChatLayout({ conversationId }: Props) {
  const [isWorkspaceOpen, setIsWorkspaceOpen] = useState(false);
  const [currentSearchId, setCurrentSearchId] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<'VN' | 'VJ' | 'QH'>('VN');
  const [externalTrigger, setExternalTrigger] = useState<string>('');

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
    <div className="flex bg-gray-100 h-screen w-full overflow-hidden text-gray-800">
      <div
        className={`h-full transition-all duration-500 ease-in-out ${
          isWorkspaceOpen ? 'z-10 w-[50%] border-r border-surface-border shadow-lg' : 'mx-auto w-full'
        }`}
      >
        <ChatWindow
          conversationId={conversationId}
          onActionDetected={handleActionDetected}
          externalInputTrigger={externalTrigger}
        />
      </div>

      <div
        className={`flex h-full flex-col bg-surface-muted transition-all duration-500 ease-in-out ${
          isWorkspaceOpen
            ? 'w-[50%] translate-x-0 opacity-100'
            : 'w-0 translate-x-full overflow-hidden opacity-0'
        }`}
      >
        {isWorkspaceOpen && currentSearchId && (
          <div className="animate-in fade-in flex h-full w-full flex-col p-6 duration-500">
            {/* Header & Tabs */}
            <div className="mb-2 shrink-0">
              <h2 className="mb-4 text-2xl font-bold tracking-tight text-slate-800">
                Danh sách chuyến bay
              </h2>
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
    </div>
  );
}