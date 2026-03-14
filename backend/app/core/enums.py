from enum import Enum

class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ComponentType(str, Enum):
    NONE = "none"
    ERROR = "error"
    DATE_PICKER = "date_picker"
    FLIGHT_LIST = "flight_list"
    CONFIRM_FORM = "confirm_form"

class ChatIntent(str, Enum):
    GREETING = "greeting"
    SEARCH_FLIGHT = "search_flight"
    PROVIDE_INFO = "provide_info"
    ANALYZE_FLIGHTS = "analyze_flights"
    FILTER_SORT_FLIGHTS = "filter_sort_flights"
    GENERAL_QUESTION = "general_question"
    OUT_OF_SCOPE = "out_of_scope"

class TravelClass(str, Enum):
    ECONOMY = "ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
from enum import Enum

class SortPreference(str, Enum):
    PRICE = "price"
    DURATION = "duration"
    DEPARTURE_TIME = "departure_time"

class AnalysisCriteria(str, Enum):
    PRICE = "PRICE"              
    DURATION = "DURATION"        
    SERVICE = "SERVICE"          
    AIRCRAFT = "AIRCRAFT"        
    TIME = "TIME"                
    FLEXIBILITY = "FLEXIBILITY"  
    AIRLINE_REPUTATION = "AIRLINE" 