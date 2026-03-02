import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from utils.llm_config import get_llm
from llama_index.core.tools import FunctionTool
from llama_index.core.agent import ReActAgent

def test_extract_info(name: str, age: int, location: str) -> str:
    """Extract information about a person."""
    print(f"TOOL CALLED: name={name}, age={age}, location={location}")
    return "Extraction complete"

tool = FunctionTool.from_defaults(fn=test_extract_info)

async def main():
    llm = get_llm()
    print("LLM Configured:", type(llm), llm.model)
    
    from llama_index.core.llms import ChatMessage
    system_msg = ChatMessage(
        role="system", 
        content="You are a helpful assistant that MUST use the provided tools to extract information. "
                "Example of how to call a tool:\n"
                "<tool_call>{'name': 'test_extract_info', 'arguments': {'name': 'John', 'age': 25, 'location': 'London'}}</tool_call>"
    )
    messages = [
        system_msg,
        ChatMessage(role="user", content="Please extract this info: My name is Ravi, I am 30 years old and I live in Mumbai. Do not say anything else, just call the tool.")
    ]
    
    # Manually pass tool metadata as dict to avoid serialization issues in this OpenAILike version
    tool_defs = [tool.metadata.to_openai_tool()]
    
    response = llm.chat(messages, tools=tool_defs)
    print("\nFull Response Trace:")
    print(response)
    print("\nMessage Content:", response.message.content)
    print("Additional Kwargs (where tool calls usually live):", response.message.additional_kwargs)

if __name__ == "__main__":
    asyncio.run(main())
