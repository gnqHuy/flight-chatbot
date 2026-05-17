import json
from core import logger, _CORE_PARAM_KEYS, _META_TTL
from services.duffel_service import search_flights_async
from services.redis_service import save_flights, save_raw, load_raw

def _normalize(val) -> str:
    if val is None or val == "" or val is False:
        return ""
    if val is True:
        return "TRUE"
    s = str(val).strip().upper()
    if s in ("TRUE", "FALSE"):
        return s if s == "TRUE" else ""
    return s

def same_core_params(params: dict, meta: dict) -> bool:
    logger.debug("[cache_check] So sánh Core Params:")
    all_same = True
    for key in _CORE_PARAM_KEYS:
        p_val = _normalize(params.get(key))
        m_val = _normalize(meta.get(key))
        if p_val != m_val:
            logger.debug(f"  [DIFF] {key}: '{meta.get(key)}' → '{params.get(key)}'")
            all_same = False
        else:
            logger.debug(f"  [SAME] {key}: '{params.get(key)}'")
    return all_same

async def recover_cache(search_id: str) -> list | None:
    logger.info(f"[recover] Bắt đầu recover cho search_id={search_id}")
    meta_raw = load_raw(f"{search_id}:meta")
    if not meta_raw:
        logger.warning(f"[recover] FAIL — không có meta key '{search_id}:meta' trong Redis")
        return None

    try:
        meta = json.loads(meta_raw)
    except Exception as e:
        logger.error(f"[recover] FAIL — parse meta lỗi: {e}")
        return None

    logger.info(
        f"[recover] Meta OK — {meta.get('origin')}→{meta.get('destination')} {meta.get('departureDate')} "
        f"adults={meta.get('adults')} children={meta.get('children')} infants={meta.get('infants')}"
    )

    try:
        logger.info("[recover] Gọi Duffel API để lấy lại vé...")
        flights = await search_flights_async(meta, max_offers=200)
        if flights:
            save_flights(flights, prefix="search", override_key=search_id)
            save_raw(f"{search_id}:meta", meta_raw, ttl=_META_TTL)
            logger.info(f"[recover] OK — {len(flights)} vé, data TTL reset 3600s, meta TTL reset {_META_TTL}s")
            return flights
        else:
            logger.warning("[recover] Duffel trả về 0 vé")
    except Exception as e:
        logger.error(f"[recover] Duffel error: {e}")
    return None