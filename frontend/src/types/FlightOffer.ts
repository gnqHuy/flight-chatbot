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
  departure: {
    iata: string;
    city: string;
    at: string;
    terminal: string;
  };
  arrival: {
    iata: string;
    city: string;
    at: string;
    terminal: string;
  };
}
