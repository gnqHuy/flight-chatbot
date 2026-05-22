import { ChatMessage } from '@/types/ChatMessage';
import { FlightOffer } from '@/types/FlightOffer';
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

  deleteConversation: async (conversationId: string) => {
    const res = await api.delete(`/conversations/${conversationId}`);
    return res.data;
  },

  renameConversation: async (conversationId: string, newTitle: string) => {
    const res = await api.patch(`/conversations/${conversationId}/title`, {
      title: newTitle,
    });
    return res.data;
  },
};