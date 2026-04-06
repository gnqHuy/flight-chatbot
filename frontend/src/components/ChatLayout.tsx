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

  // 🌟 SỬA: Đổi default tab thành 'VN' và giới hạn kiểu dữ liệu
  const [activeTab, setActiveTab] = useState<'VN' | 'VJ' | 'QH'>('VN');

  const [externalTrigger, setExternalTrigger] = useState<string>('');

  const handleActionDetected = (action: any) => {
    if (
      action &&
      (action.type === 'flight_list' || action.type === 'FLIGHT_LIST') &&
      action.payload?.search_id
    ) {
      setCurrentSearchId(action.payload.search_id);
      setIsWorkspaceOpen(true);
    }
  };

  const handlePromptClick = (promptText: string) => {
    setExternalTrigger(`${promptText} `);
  };

  // 🌟 MỚI: Xử lý sự kiện khi API Resume (so sánh vé) gọi xong
  const handleCompareComplete = (botResponse: any) => {
    console.log('Đã so sánh xong, response từ Backend:', botResponse);
    // TODO: Tùy thuộc vào cách ChatWindow của bạn hoạt động,
    // bạn có thể gọi một hàm để ép ChatWindow re-fetch lại danh sách tin nhắn,
    // hoặc trigger một tín hiệu giả vào externalTrigger để ChatWindow cập nhật.
    // VD: setExternalTrigger(`[REFRESH_CHAT]_${Date.now()}`);
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-white text-gray-800">
      <div
        className={`h-full transition-all duration-500 ease-in-out ${
          isWorkspaceOpen ? 'z-10 w-[50%] border-r border-gray-200 shadow-lg' : 'mx-auto w-full'
        }`}
      >
        <ChatWindow
          conversationId={conversationId}
          onActionDetected={handleActionDetected}
          externalInputTrigger={externalTrigger}
        />
      </div>

      <div
        className={`flex h-full flex-col bg-[#F8FAFC] transition-all duration-500 ease-in-out ${
          isWorkspaceOpen
            ? 'w-[50%] translate-x-0 opacity-100'
            : 'w-0 translate-x-full overflow-hidden opacity-0'
        }`}
      >
        {isWorkspaceOpen && currentSearchId && (
          <div className="animate-in fade-in flex h-full w-full flex-col p-6 duration-500">
            {/* 1. Header & Tabs */}
            <div className="mb-4 shrink-0">
              <h2 className="mb-4 text-2xl font-bold tracking-tight text-slate-800">
                Danh sách chuyến bay
              </h2>
              <div className="flex space-x-1 border-b border-gray-200">
                {/* 🌟 SỬA: Đã xóa object { id: 'ALL', label: 'Tất cả' } */}
                {[
                  { id: 'VN', label: 'Vietnam Airlines' },
                  { id: 'VJ', label: 'Vietjet Air' },
                  { id: 'QH', label: 'Bamboo Airways' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`rounded-t-lg px-5 py-2.5 text-sm font-semibold transition-all ${
                      activeTab === tab.id
                        ? 'border-b-2 border-blue-600 bg-white text-blue-600 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]'
                        : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* 2. Danh sách vé thực tế */}
            <div className="scrollbar-thin scrollbar-thumb-gray-300 flex-1 overflow-y-auto pr-2">
              <FlightListContainer
                conversationId={conversationId}
                searchId={currentSearchId}
                activeTab={activeTab}
                onAskAI={handlePromptClick}
                onCompareComplete={handleCompareComplete}
              />
            </div>

            {/* 3. Prompt Chips */}
            <div className="mt-4 shrink-0 border-t border-gray-200 bg-[#F8FAFC] pt-4">
              <p className="mb-3 text-[11px] font-bold tracking-widest text-slate-400 uppercase">
                💡 Gợi ý thao tác nhanh
              </p>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handlePromptClick('Chỉ hiển thị các chuyến bay vào buổi sáng')}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm transition-all hover:border-blue-400 hover:text-blue-600"
                >
                  🌅 Bay buổi sáng
                </button>
                <button
                  onClick={() => handlePromptClick('Sắp xếp danh sách ưu tiên giá rẻ nhất')}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm transition-all hover:border-blue-400 hover:text-blue-600"
                >
                  💰 Rẻ nhất lên đầu
                </button>
                <button
                  onClick={() => handlePromptClick('Lọc ra các chuyến bay thẳng, không quá cảnh')}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm transition-all hover:border-blue-400 hover:text-blue-600"
                >
                  ⚡ Bay thẳng
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
