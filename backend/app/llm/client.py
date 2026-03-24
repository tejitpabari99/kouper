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
    """Extract and join text-type blocks from LLM assistant content, before tool use."""
    parts = []
    for block in content_list:
        if hasattr(block, 'type') and block.type == 'text':
            parts.append(block.text)
        elif isinstance(block, dict) and block.get('type') == 'text':
            parts.append(block.get('text', ''))
    return ' '.join(parts).strip()


def chat(message: str, conversation_history: list, patient: Optional[dict] = None, session=None, page_context: str = "") -> tuple[str, list]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    client = anthropic.Anthropic(api_key=api_key)

    patient_context = build_patient_context(patient)
    system_prompt = build_system_prompt(patient_context, session=session)
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
            tool_results = []
            assistant_content = []
            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
                    result = execute_tool(block.name, block.input, session_patient=patient)
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
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

            history = history + [
                {"role": "assistant", "content": assistant_content},
                {"role": "user", "content": tool_results},
            ]
        else:
            final_text = ""
            assistant_content = []
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
                    assistant_content.append({"type": "text", "text": block.text})
            history = history + [{"role": "assistant", "content": assistant_content}]
            return final_text, history
