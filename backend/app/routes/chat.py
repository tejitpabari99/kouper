"""
Chat route — the primary entry point for the nurse-to-LLM conversation.

Receives a nurse message, runs it through the LLM tool-use loop, persists
the updated conversation history back to the session, and returns the
assistant's reply alongside the full updated session state (so the frontend
can reactively update the UI without a separate state fetch).
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..session_store import store
from ..llm.client import chat

router = APIRouter(prefix="/session", tags=["chat"])

class MessageRequest(BaseModel):
    message: str
    page_context: str = ""  # Optional: which screen the nurse is on (e.g. "insurance", "booking")

@router.post("/{session_id}/message")
def send_message(session_id: str, body: MessageRequest):
    """
    Send a nurse message to the LLM and return the assistant's response.

    Loads the existing conversation history from the session so the model
    maintains full context across turns.  After the LLM responds, the updated
    history (including any tool call turns) is written back to the session.

    Returns both the response text and the full session object so the frontend
    can update booking state reactively if the LLM triggered any changes via
    tool calls.
    """
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        response_text, updated_history = chat(
            message=body.message,
            conversation_history=session.conversation_history,
            patient=session.patient,
            session=session,
            page_context=body.page_context,
        )
        session.conversation_history = updated_history
        store.update(session)
        return {"response": response_text, "session": session}
    except ValueError as e:
        # Raised when ANTHROPIC_API_KEY is missing or configuration is invalid
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        import logging
        logging.error(f"Chat route unhandled error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="The assistant encountered an unexpected error. Please try your message again."
        )
