"""
services/airline_service.py
Lấy thông tin hãng bay từ PostgreSQL (raw psycopg2, không import từ backend).
"""
import os
import logging
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "")


def _get_conn():
    """Tạo connection psycopg2 từ DATABASE_URL."""
    import re
    # postgresql://user:pass@host:port/db
    m = re.match(
        r"postgresql(?:\+psycopg2)?://([^:]+):([^@]+)@([^:/]+):(\d+)/(.+)",
        DB_URL,
    )
    if not m:
        raise ValueError(f"DATABASE_URL không hợp lệ: {DB_URL}")
    user, password, host, port, dbname = m.groups()
    return psycopg2.connect(
        host=host, port=int(port), dbname=dbname,
        user=user, password=password,
        connect_timeout=5,
    )


def get_airlines_info(airline_codes: list[str] | None = None) -> str:
    """
    Lấy thông tin ưu/nhược điểm và hành lý của hãng từ DB.
    Trả về string context cho LLM.
    """
    try:
        with _get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                if airline_codes:
                    codes = [c.upper() for c in airline_codes if c and c != "CLEAR"]
                    if not codes:
                        return ""
                    cur.execute(
                        "SELECT code, name, description, pros, cons, baggage_basic_info "
                        "FROM airlines WHERE code = ANY(%s)",
                        (codes,),
                    )
                else:
                    cur.execute(
                        "SELECT code, name, description, pros, cons, baggage_basic_info "
                        "FROM airlines"
                    )
                rows = cur.fetchall()

        if not rows:
            return ""

        parts = []
        for row in rows:
            lines = [f"--- Hãng {row['name']} ({row['code']}) ---"]
            if row["description"]:
                lines.append(f"Mô tả: {row['description']}")
            if row["pros"]:
                pros = row["pros"] if isinstance(row["pros"], list) else []
                lines.append(f"Ưu điểm: {' | '.join(pros)}")
            if row["cons"]:
                cons = row["cons"] if isinstance(row["cons"], list) else []
                lines.append(f"Nhược điểm/Lưu ý: {' | '.join(cons)}")
            if row["baggage_basic_info"]:
                lines.append(f"Hành lý: {row['baggage_basic_info']}")
            parts.append("\n".join(lines))

        return "\n\n".join(parts)

    except Exception as e:
        logger.error(f"[AirlineService] DB error: {e}")
        return ""