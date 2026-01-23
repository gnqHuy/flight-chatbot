'use client';

import { use } from 'react';
import ChatWindow from '@/components/ChatWindow';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ChatPage({ params }: PageProps) {
  const { id } = use(params);

  return <ChatWindow conversationId={id} />;
}
