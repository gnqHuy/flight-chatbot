// Nơi đi/Nơi đến
export interface FlightEndpoint {
  iata: string;
  city?: string; // Có thể optional vì bên trong segmentDetails không map city
  at: string;
  terminal: string;
}

// Chi tiết từng chặng bay (segment)
export interface SegmentDetail {
  carrierCode: string;
  operatingCarrier: string;
  isCodeshare: boolean;
  flightNumber: string;
  aircraft: string;
  duration: string;
  layoverTime?: string;
  cabin: string;
  bookingClass: string;
  fareBasis: string;
  departure: FlightEndpoint;
  arrival: FlightEndpoint;
}

// Thông tin 1 chiều bay (có thể gồm nhiều chặng/segments)
export interface Itinerary {
  duration: string;
  stops: number;
  flightNumber: string;
  departure: FlightEndpoint;
  arrival: FlightEndpoint;
  segmentDetails: SegmentDetail[];
}

// Cấu trúc tổng thể của 1 vé
export interface FlightOffer {
  id: string;
  price: number;
  basePrice: number;
  taxAndFees: number;
  currency: string;
  cabin: string;
  fareOption: string;
  bookableSeats: number | string;
  lastTicketingDate: string;
  validatingAirline: string;
  checkedBaggage: string;
  cabinBaggage: string;
  airlines: string[];
  itineraries: Itinerary[];
}
