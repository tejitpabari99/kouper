import os
import anthropic
from dotenv import load_dotenv
from typing import Optional
from .tools import TOOLS
from .prompts import build_system_prompt, build_patient_context
from .tool_executor import execute_tool

load_dotenv('/root/projects/kouper/.env')

def chat(message: str, conversation_history: list, patient: Optional[dict] = None) -> tuple[str, list]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    client = anthropic.Anthropic(api_key=api_key)

    patient_context = build_patient_context(patient)
    system_prompt = build_system_prompt(patient_context)
    history = conversation_history + [{"role": "user", "content": message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
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
