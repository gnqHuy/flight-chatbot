import { Role } from './enums/Role';
import { ComponentType } from './enums/ComponentType';

export interface FlightListPayload {
  search_id: string;
}

export interface ErrorPayload {
  msg: string;
}

export type ChatAction =
  | { type: ComponentType.FLIGHT_LIST | 'flight_list'; payload: FlightListPayload }
  | { type: ComponentType.ERROR | 'error'; payload: ErrorPayload };

export interface ChatMessage {
  conversation_id: string;
  message_id: string;
  role: Role;
  content: string;
  intent: string;
  action: ChatAction | null;
  created_at: string;
}
