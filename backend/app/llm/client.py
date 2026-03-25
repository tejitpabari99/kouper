"""
LLM conversation loop for the Care Coordinator assistant.

This module owns the agentic tool-use loop: it sends messages to Claude,
handles tool-call responses by executing the requested tools, feeds results
back, and repeats until the model produces a final text reply.
"""
import os
import anthropic
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional
from .tools import TOOLS
from .prompts import build_system_prompt, build_patient_context
from .tool_executor import execute_tool
from ..audit_log import append_audit_entry, AuditLogEntry

load_dotenv('/root/projects/kouper/.env')


def _extract_text_blocks(content_list) -> str:
    """
    Pull the text portions from a mixed assistant content block list.

    The Anthropic API may return a response that contains both text blocks
    (the model's "thinking out loud") and tool_use blocks in the same turn.
    This helper extracts only the text so it can be stored as reasoning_hint
    in the audit log alongside the tool call.
    """
    parts = []
    for block in content_list:
        if hasattr(block, 'type') and block.type == 'text':
            parts.append(block.text)
        elif isinstance(block, dict) and block.get('type') == 'text':
            parts.append(block.get('text', ''))
    return ' '.join(parts).strip()


def chat(message: str, conversation_history: list, patient: Optional[dict] = None, session=None, page_context: str = "") -> tuple[str, list]:
    """
    Send a nurse message to the LLM and return the final assistant reply.

    Implements the Anthropic tool-use agentic loop:
      1. Append the user message to the conversation history.
      2. Call the model. If it responds with tool_use, execute every requested
         tool, append both the assistant turn and the tool results, then loop.
      3. When stop_reason is "end_turn" (no more tools needed), return the
         text response and the full updated history.

    The full conversation history is threaded through so the model retains
    context across multiple nurse messages in the same session.

    Args:
        message: The nurse's latest chat message.
        conversation_history: Prior turns in Anthropic message format.
        patient: Current patient dict from the session (injected into context).
        session: The BookingSession object — used to surface session state
                 (step, pending referrals, confirmed bookings) in the prompt.
        page_context: Optional string describing which screen the nurse is on,
                      appended to the system prompt to allow context-aware replies.

    Returns:
        (reply_text, updated_history) where updated_history includes all new turns.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    client = anthropic.Anthropic(api_key=api_key)

    patient_context = build_patient_context(patient)
    system_prompt = build_system_prompt(patient_context, session=session)
    # Append screen context when the frontend tells us which page the nurse is on.
    # This lets the model give more relevant guidance (e.g., "you're on the
    # insurance screen" vs. "you're on the booking confirmation screen").
    if page_context:
        system_prompt += f"\n\n## Current Screen Context\n{page_context}"
    history = conversation_history + [{"role": "user", "content": message}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=system_prompt,
            tools=TOOLS,
            messages=history,
        )

        if response.stop_reason == "tool_use":
            # The model wants to call one or more tools.  Build the assistant
            # turn (which must include both text and tool_use blocks) then
            # execute each tool and collect results.
            tool_results = []
            assistant_content = []
            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
                    result = execute_tool(block.name, block.input, session_patient=patient)
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
                    # Audit every tool call: record inputs, outputs, and any
                    # reasoning text the model produced in the same turn.
                    append_audit_entry(AuditLogEntry(
                        timestamp=datetime.utcnow().isoformat() + "Z",
                        type="llm",
                        session_id=session.session_id if session else "unknown",
                        tool_name=block.name,
                        tool_input=dict(block.input) if hasattr(block.input, '__iter__') else {},
                        tool_output=result,
                        reasoning_hint=_extract_text_blocks(response.content),
                        error='"error": true' in result or '"error":true' in result,
                        error_code=None,
                    ))

            # Anthropic requires tool results to be injected as a "user" turn
            # immediately following the assistant turn that requested them.
            history = history + [
                {"role": "assistant", "content": assistant_content},
                {"role": "user", "content": tool_results},
            ]
        else:
            # Model has finished — collect any text blocks and return.
            final_text = ""
            assistant_content = []
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
                    assistant_content.append({"type": "text", "text": block.text})
            history = history + [{"role": "assistant", "content": assistant_content}]
            return final_text, history
