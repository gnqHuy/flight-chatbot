from enum import Enum

class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ComponentType(str, Enum):
    NONE = "none"
    DATE_PICKER = "date_picker"
    FLIGHT_LIST = "flight_list"
    CONFIRM_FORM = "confirm_form"

class ChatIntent(str, Enum):
    GREETING = "greeting"
    SEARCH_FLIGHT = "search_flight"
    BOOK_TICKET = "book_ticket"
    PROVIDE_INFO = "provide_info"
    FILTER_RESULT = "filter_result"
    COMPARE_FLIGHTS = "compare_flights"
    ASK_DETAIL = "ask_detail"
    GENERAL_QUESTION = "general_question"
    OUT_OF_SCOPE = "out_of_scope"