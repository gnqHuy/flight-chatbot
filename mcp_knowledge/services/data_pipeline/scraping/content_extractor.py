"""
services/data_pipeline/scraping/content_extractor.py
"""
import re
import hashlib
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

NOISE_TAGS = [
    "script", "style", "noscript",
    "nav", "header", "footer",
    "iframe", "svg", "canvas",
]

MIN_CONTENT_LENGTH = 200


def extract_content(html: str) -> str | None:
    """
    Lấy toàn bộ text từ trang sau khi xóa structural noise tags.
    LLM ở bước sau sẽ lo việc lọc nội dung không liên quan.
    """
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Xóa structural noise
    for tag in NOISE_TAGS:
        for el in soup.find_all(tag):
            el.decompose()

    # Xử lý ảnh icon VJ (tick/cross → text)
    for img in soup.find_all("img"):
        src = img.get("src", "").lower()
        alt = img.get("alt", "").strip()
        if "greensuccess" in src or "tick" in src or "check" in src:
            img.replace_with(" [Bao gồm] ")
        elif "redclose" in src or "cross" in src:
            img.replace_with(" [Không bao gồm] ")
        elif alt:
            img.replace_with(f" [{alt}] ")
        else:
            img.decompose()

    # Table → giữ cấu trúc bằng separator
    for tr in soup.find_all("tr"):
        for cell in tr.find_all(["td", "th"]):
            cell.append(" | ")
        tr.append("\n")

    # Heading → prefix
    for h in soup.find_all(["h1", "h2", "h3", "h4", "h5"]):
        h.insert(0, f"\n{'#' * int(h.name[1])} ")
        h.append("\n")

    # List item → dash
    for li in soup.find_all("li"):
        li.insert(0, "\n- ")

    # Lấy toàn bộ text
    raw   = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    clean = "\n".join(lines)
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    clean = re.sub(r"\|\s+\|\s+\|", "|", clean)

    if len(clean) < MIN_CONTENT_LENGTH:
        logger.warning(f"[extractor] Content too short: {len(clean)} chars")
        return None

    return clean.strip()


def compute_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()