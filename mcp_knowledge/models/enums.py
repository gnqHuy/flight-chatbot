from enum import Enum

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