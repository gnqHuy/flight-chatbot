import { Role } from './enums/Role';
import { ComponentType } from './enums/ComponentType';

export interface FlightLocation {
  iata: string;
  city: string;
  at: string;
  terminal: string;
}

export interface FlightOffer {
  id: string;
  price: number;
  currency: string;
  cabin: string;
  baggage: string;
  duration: string;
  stops: number;
  airlines: string[];
  flightNumber: string;
  departure: FlightLocation;
  arrival: FlightLocation;
}

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
