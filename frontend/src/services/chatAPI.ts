import { ChatMessage } from '@/types/ChatMessage';
import api from '@/utils/api';

export const chatAPI = {
  getHistory: async (conversationId: string) => {
    const res = await api.get<ChatMessage[]>(`/conversations/${conversationId}/messages`);
    return res.data;
  },

  sendMessage: async (conversationId: string, content: string) => {
    const res = await api.post(`/conversations/${conversationId}/messages`, {
      content: content,
    });
    return res.data;
  },
};
