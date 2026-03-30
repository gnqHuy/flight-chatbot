'use client';

import { use } from 'react';
import ChatLayout from '@/components/ChatLayout';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ChatPage({ params }: PageProps) {
  const { id } = use(params);

  return <ChatLayout conversationId={id} />;
}
