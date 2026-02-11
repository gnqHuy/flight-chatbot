import json
from pathlib import Path

class I18nService:
    def __init__(self):
        self.airports = {}
        self.messages = {}
        self._load_data()

    def _load_data(self):
        current_dir = Path(__file__).resolve().parent
        
        try:
            with open(current_dir / "i18n" / "airports.json", "r", encoding="utf-8") as f:
                self.airports = json.load(f)
        except Exception as e:
            print(f"Lỗi load airports.json: {e}")

        try:
            with open(current_dir / "i18n" / "messages.json", "r", encoding="utf-8") as f:
                self.messages = json.load(f)
        except Exception as e:
            print(f"Lỗi load messages.json: {e}")

    def get_city(self, iata_code: str, lang: str = "vi") -> str:
        """Map mã IATA thành tên thành phố theo ngôn ngữ."""
        if not iata_code:
            return ""
        code_upper = iata_code.upper()
        if code_upper in self.airports:
            return self.airports[code_upper].get(lang, code_upper)
        return code_upper

    def get_msg(self, msg_key: str, lang: str = "vi", **kwargs) -> str:
        """Lấy câu thoại của bot và điền tham số (origin, dest, date...)."""
        if msg_key in self.messages:
            template = self.messages[msg_key].get(lang, "")
            return template.format(**kwargs)
        return msg_key

    def get_field_name(self, field_key: str, lang: str = "vi") -> str:
        """Dịch tên các trường (VD: origin -> điểm đi)."""
        fields = self.messages.get("fields", {})
        if field_key in fields:
            return fields[field_key].get(lang, field_key)
        return field_key

i18n = I18nService()