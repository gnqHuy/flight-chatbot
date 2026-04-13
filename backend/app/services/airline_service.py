from sqlmodel import Session
from app.database.database import engine
from app.repositories.airline_repo import AirlineRepository

class AirlineService:
    def get_airlines_analysis_context(self, airline_codes: list[str] = None) -> str:
        """
        Lấy thông tin ưu/nhược điểm và hành lý của các hãng bay để làm context cho AI.
        Nếu không truyền airline_codes, mặc định lấy tất cả hãng trong DB.
        """
        with Session(engine) as session:
            repo = AirlineRepository(session)
            
            airlines = []
            if not airline_codes or airline_codes == ["CLEAR"]:
                airlines = repo.get_all()
            else:
                for code in airline_codes:
                    al = repo.get_by_code(code)
                    if al:
                        airlines.append(al)
                        
            if not airlines:
                return ""
                
            context = ""
            for al in airlines:
                context += f"--- Hãng {al.name} ({al.code}) ---\n"
                
                if al.description:
                    context += f"Mô tả: {al.description}\n"
                    
                if al.pros:
                    pros_str = " | ".join(al.pros)
                    context += f"Ưu điểm: {pros_str}\n"
                    
                if al.cons:
                    cons_str = " | ".join(al.cons)
                    context += f"Nhược điểm/Lưu ý: {cons_str}\n"
                    
                if al.baggage_basic_info:
                    context += f"Hành lý: {al.baggage_basic_info}\n"
                    
                context += "\n"
            
            return context

airline_service = AirlineService()