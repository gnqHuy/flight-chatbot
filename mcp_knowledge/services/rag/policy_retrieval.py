import logging
from collections import defaultdict
from services.rag.vector_store import get_policy_vector_store

logger = logging.getLogger(__name__)
SUPPORTED_AIRLINES = ["VN", "VJ", "QH"]


def retrieve_policy(query: str, target_airlines: list[str] | None = None) -> str:
    store = get_policy_vector_store()
    docs  = []
    for al in (target_airlines or SUPPORTED_AIRLINES):
        k = 3 if target_airlines else 2
        docs.extend(store.similarity_search(query, k=k, filter={"airline": al.upper()}))

    if not docs: return ""

    grouped = defaultdict(list)
    for doc in docs:
        airline = doc.metadata.get("airline","UNKNOWN").upper()
        url     = doc.metadata.get("source_url","Không có link")
        content = " ".join(doc.page_content.replace("\n"," ").split()).strip()
        if not any(i["content"] == content for i in grouped[airline]):
            grouped[airline].append({"content": content, "url": url})

    result = f"[KIẾN THỨC NGHIỆP VỤ CHÍNH SÁCH]\n- CÂU HỎI: '{query}'\n- NỘI DUNG:\n"
    for airline, items in grouped.items():
        result += f"\n▶ QUY ĐỊNH HÃNG {airline}:\n"
        for i, item in enumerate(items, 1):
            result += f"  {i}. {item['content']}\n     [Link]: {item['url']}\n"
    return result.strip()