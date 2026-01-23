export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'bot';
  created_at: string;
}
