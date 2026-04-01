from enum import Enum

class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ComponentType(str, Enum):
    NONE = "none"
    ERROR = "error"
    FLIGHT_LIST = "flight_list"

class ChatIntent(str, Enum):
    SEARCH_FLIGHT = "search_flight"
    ANALYZE_FLIGHTS = "analyze_flights"
    FILTER_SORT_FLIGHTS = "filter_sort_flights"
    GENERAL_QUESTION = "general_question"
    PROMO_SEARCH = "promo_search"
    OUT_OF_SCOPE = "out_of_scope"

class TravelClass(str, Enum):
    ECONOMY = "ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"

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

class UrlType(str, Enum):
    POLICY_PAGE = "policy_page"
    PROMO_LIST_PAGE = "promo_list_page"
    PROMO_PAGE = "promo_page"

class StagingStatus(str, Enum):
    PENDING = "PENDING"
    CRAWLED = "CRAWLED"
    LLM_FORMATTED = "LLM_FORMATTED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"