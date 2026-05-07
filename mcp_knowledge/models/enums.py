from enum import Enum


class UrlType(str, Enum):
    SITEMAP_PAGE    = "sitemap_page"
    POLICY_PAGE     = "policy_page"
    PROMO_LIST_PAGE = "promo_list_page" 
    PROMO_PAGE      = "promo_page"


class PolicyCategory(str, Enum):
    BAGGAGE          = "baggage"
    CHECK_IN         = "check_in"
    FARE_CONDITIONS  = "fare_conditions"
    SPECIAL_SERVICES = "special_services"
    EXPERIENCE       = "experience"
    AIRPORT          = "airport"
    LEGAL            = "legal"
    SUPPORT          = "support"
    ADDITIONAL       = "additional"
    PROMOTION        = "promotion"
    TRAVEL_ADVICE    = "travel_advice"
    BOOKING_GUIDE    = "booking_guide"
    GENERAL          = "general"

class StagingStatus(str, Enum):
    PENDING       = "PENDING"
    CRAWLED       = "CRAWLED"
    LLM_FORMATTED = "LLM_FORMATTED"
    COMPLETED     = "COMPLETED"
    ERROR         = "ERROR"