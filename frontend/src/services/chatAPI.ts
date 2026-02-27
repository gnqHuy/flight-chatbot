import { ChatMessage, FlightOffer } from '@/types/ChatMessage'; // Nhớ import thêm FlightOffer nếu file đó chứa type
import api from '@/utils/api';

export const chatAPI = {
  getHistory: async (conversationId: string) => {
    const res = await api.get<ChatMessage[]>(`/conversations/${conversationId}/messages`);
    return res.data;
  },

  sendMessage: async (conversationId: string, content: string) => {
    const res = await api.post(`/conversations/${conversationId}/messages`, {
      message: content,
    });
    return res.data;
  },

  createConversation: async (title: string = 'New Chat') => {
    const res = await api.post('/conversations/', { title });
    return res.data;
  },

  getConversations: async () => {
    const res = await api.get('/conversations/');
    return res.data;
  },

  getCachedFlights: async (searchId: string) => {
    const res = await api.get<{ flights: FlightOffer[] }>(`/flights/cache/${searchId}`);
    return res.data;
  },
};
