from enum import Enum

class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ComponentType(str, Enum):
    NONE = "none"
    ERROR = "error"
    FLIGHT_LIST = "flight_list"
    REQUIRE_FLIGHT_SELECTION = "require_flight_selection"
    APPLY_FILTERS = "apply_filters"

class TravelClass(str, Enum):
    ECONOMY = "ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"

class SortPreference(str, Enum):
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    DEPARTURE_TIME = "departure_time"
    ARRIVAL_TIME = "arrival_time"

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