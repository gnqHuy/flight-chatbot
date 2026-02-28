from app.ai.graph.state import ChatState
from app.core.i18n_service import i18n
from app.ai.llm.llm import llm
from langchain_core.prompts import ChatPromptTemplate

def final_response_node(state: ChatState):
    lang = state.language or "vi"
    intent = state.intent

    if intent == "greeting":
        return {"response_text": i18n.get_msg("greeting_response", lang=lang)}
        
    if intent == "out_of_scope":
        return {"response_text": i18n.get_msg("ood_response", lang=lang)}

    if intent == "general_question":
        context = getattr(state, "context", "")
        
        if not context:
            return {"response_text": i18n.get_msg("unknown_intent", lang=lang)}

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a professional aviation assistant. Use the following regulations to answer the customer's question in {lang}. If the information is not in the regulations, say you don't know, do not hallucinate.\n\nRegulations:\n{context}"),
            ("human", "{question}")
        ])
        
        chain = prompt | llm
        response = chain.invoke({
            "context": context, 
            "question": state.user_message,
            "lang": lang
        })
        
        return {"response_text": response.content}

    if intent in ["search_flight", "provide_info"]:
        if state.error_msg:
            return {"response_text": i18n.get_msg("api_error", lang=lang) or state.error_msg}

        if state.action and state.action.get("type") == "flight_list":
            city_origin = i18n.get_city(state.origin, lang) if state.origin else state.origin
            city_dest = i18n.get_city(state.destination, lang) if state.destination else state.destination
            
            flight_count = state.action.get("payload", {}).get("count", "các")
            response = i18n.get_msg(
                "flight_found", 
                lang=lang, 
                origin=city_origin, 
                dest=city_dest, 
                date=state.departureDate,
                count=flight_count
            )
            return {"response_text": response}

        missing_slots = []
        required_slots = ["origin", "destination", "departureDate"]
        for slot in required_slots:
            if not getattr(state, slot, None):
                missing_slots.append(i18n.get_field_name(slot, lang))
                
        if missing_slots:
            missing_str = ", ".join(missing_slots)
            return {
                "response_text": i18n.get_msg("ask_missing_info", lang=lang, missing_str=missing_str)
            }

    return {"response_text": i18n.get_msg("unknown_intent", lang=lang)}