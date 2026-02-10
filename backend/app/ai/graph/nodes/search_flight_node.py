from app.ai.graph.state import ChatState
from app.services.flight_service import flight_service

def search_flights_node(state: ChatState):
    print("--- NODE: SEARCHING FLIGHTS ---" , state, "\n")
    
    # origin = state.origin
    # destination = state.destination
    # departureDate = state.departureDate
    
    # try:
    #     flights = flight_service.search_flights(origin, destination, departureDate)
        
    #     if not flights:
    #          return {
    #             "search_results": [],
    #             "error_msg": f"Không tìm thấy vé từ {origin} đi {destination} ngày {departureDate}"
    #         }
            
    #     return {
    #         "search_results": flights,
    #         "error_msg": None
    #     }

    # except Exception as e:
    #     return {
    #         "search_results": [],
    #         "error_msg": str(e)
    #     }
    return state