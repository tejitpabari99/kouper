from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..session_store import store
from ..llm.client import chat

router = APIRouter(prefix="/session", tags=["chat"])

class MessageRequest(BaseModel):
    message: str

@router.post("/{session_id}/message")
def send_message(session_id: str, body: MessageRequest):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        response_text, updated_history = chat(
            message=body.message,
            conversation_history=session.conversation_history,
            patient=session.patient,
        )
        session.conversation_history = updated_history
        store.update(session)
        return {"response": response_text, "session": session}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")
