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
    COMPARE_FLIGHTS = "compare_flights"
    PRICE_ANALYSIS = "price_analysis"
    GENERAL_QUESTION = "general_question"
    OUT_OF_SCOPE = "out_of_scope"

class TravelClass(str, Enum):
    ECONOMY = "economy"
    BUSINESS = "business"
    FIRST = "first"
    