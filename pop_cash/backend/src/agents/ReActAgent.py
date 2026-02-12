from llama_index.core.llms import ChatMessage
from llama_index.core.tools import ToolSelection, ToolOutput
from llama_index.core.workflow import Event
from llama_index.core import Settings
from llama_index.protocols.ag_ui.agent import StateSnapshotWorkflowEvent, ToolCallResultEvent
from src.agents.ToolCallResultWorkflowEvent import ToolCallResultWorkflowEvent
import uuid

class PrepEvent(Event):
    pass


class InputEvent(Event):
    input: list[ChatMessage]


class StreamEvent(Event):
    delta: str


class ToolCallEvent(Event):
    tool_calls: list[ToolSelection]


class FunctionOutputEvent(Event):
    output: ToolOutput

from typing import Any, List

from llama_index.core.agent.react import ReActChatFormatter, ReActOutputParser
from llama_index.core.agent.react.types import (
    ActionReasoningStep,
    ObservationReasoningStep,
)
from llama_index.core.llms.llm import LLM
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools.types import BaseTool
from llama_index.core.workflow import (
    Context,
    Workflow,
    StartEvent,
    StopEvent,
    step,
)
from llama_index.llms.openai import OpenAI


class ReActAgent(Workflow):
    def __init__(
        self,
        *args: Any,
        system_prompt: str | None = None,
        llm: LLM | None = None,
        tools: list[BaseTool] | None = None,
        extra_context: str | None = None,
        broadcast_tool_result: List[str] = [],
        max_iterations: int = 5,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.tools = tools or []
        self.llm = llm or Settings.llm
        self.max_iterations = max_iterations
        self.formatter = ReActChatFormatter.from_defaults(
            context=extra_context or ""
        )
        self.system_prompt = system_prompt 
        self.output_parser = ReActOutputParser()

    @step
    async def new_user_msg(self, ctx: Context, ev: StartEvent) -> PrepEvent:
        # clear sources
        await ctx.store.set("sources", [])
        if ev.parent_ctx:
            self.ctx = ev.parent_ctx
        else:
            self.ctx = ctx

        # init memory if needed
        memory = await ctx.store.get("memory", default=None)
        if not memory:
            memory = ChatMemoryBuffer.from_defaults(llm=self.llm)

        # get user input
        user_input = ev.input
        if self.system_prompt:
            memory.put(ChatMessage(role="system", content=self.system_prompt))
        user_msg = ChatMessage(role="user", content=user_input)
        print(f"DEBUG: New User Message: {user_input}")
        memory.put(user_msg)

        # clear current reasoning
        await ctx.store.set("current_reasoning", [])

        # set memory
        await ctx.store.set("memory", memory)
        await ctx.store.set("num_iterations", 0)

        return PrepEvent()

    @step
    async def prepare_chat_history(
        self, ctx: Context, ev: PrepEvent
    ) -> InputEvent:
        # get chat history
        memory = await ctx.store.get("memory")
        chat_history = memory.get()
        current_reasoning = await ctx.store.get(
            "current_reasoning", default=[]
        )
        num_iterations = await ctx.store.get("num_iterations", default=0)
        num_iterations += 1
        await ctx.store.set("num_iterations", num_iterations)

        if num_iterations > self.max_iterations:
            print(f"DEBUG: Max iterations reached ({num_iterations} > {self.max_iterations}). Using summary fallback.")
            # Use original chat history and add a summarizing system message
            summary_history = chat_history + [
                ChatMessage(
                    role="system", 
                    content="The task is taking too long to complete. Please provide a final answer or summary based on the information gathered so far, without calling more tools."
                )
            ]
            await ctx.store.set("limit_reached", True)
            return InputEvent(input=summary_history)

        # format the prompt with react instructions
        llm_input = self.formatter.format(
            self.tools, chat_history, current_reasoning=current_reasoning
        )
        await ctx.store.set("limit_reached", False)
        return InputEvent(input=llm_input)

    @step
    async def handle_llm_input(
        self, ctx: Context, ev: InputEvent
    ) -> ToolCallEvent | StopEvent:
        chat_history = ev.input
        current_reasoning = await ctx.store.get(
            "current_reasoning", default=[]
        )
        memory = await ctx.store.get("memory")

        response_gen = await self.llm.astream_chat(chat_history,
        stream_options={"include_usage": True})
        
        async for response in response_gen:
            ctx.write_event_to_stream(StreamEvent(delta=response.delta or ""))
        
        print(f"DEBUG: LLM Response Raw: {response.message.content}")

        try:
            limit_reached = await ctx.store.get("limit_reached", default=False)
            if limit_reached:
                print("DEBUG: Limit reached, skipping ReAct parsing.")
                memory.put(
                    ChatMessage(
                        role="assistant", content=response.message.content
                    )
                )
                await ctx.store.set("memory", memory)
                return StopEvent(
                    result={
                        "response": response.message.content,
                        "sources": [await ctx.store.get("sources", default=[])],
                        "reasoning": current_reasoning,
                    }
                )

            reasoning_step = self.output_parser.parse(response.message.content)
            print(f"DEBUG: Parsed Reasoning Step: {reasoning_step}")
            current_reasoning.append(reasoning_step)

            if reasoning_step.is_done:
                memory.put(
                    ChatMessage(
                        role="assistant", content=reasoning_step.response
                    )
                )
                await ctx.store.set("memory", memory)
                await ctx.store.set("current_reasoning", current_reasoning)

                sources = await ctx.store.get("sources", default=[])

                return StopEvent(
                    result={
                        "response": reasoning_step.response,
                        "sources": [sources],
                        "reasoning": current_reasoning,
                    }
                )
            elif isinstance(reasoning_step, ActionReasoningStep):
                tool_name = reasoning_step.action
                tool_args = reasoning_step.action_input
                print(f"DEBUG: Tool Call Requested: {tool_name} with args: {tool_args}")
                return ToolCallEvent(
                    tool_calls=[
                        ToolSelection(
                            tool_id="fake",
                            tool_name=tool_name,
                            tool_kwargs=tool_args,
                        )
                    ]
                )
        except Exception as e:
            current_reasoning.append(
                ObservationReasoningStep(
                    observation=f"There was an error in parsing my reasoning: {e}"
                )
            )
            await ctx.store.set("current_reasoning", current_reasoning)

        # if no tool calls or final response, iterate again
        return PrepEvent()

    @step
    async def handle_tool_calls(
        self, ctx: Context, ev: ToolCallEvent
    ) -> PrepEvent:
        tool_calls = ev.tool_calls
        tools_by_name = {tool.metadata.get_name(): tool for tool in self.tools}
        current_reasoning = await ctx.store.get(
            "current_reasoning", default=[]
        )
        sources = await ctx.store.get("sources", default=[])

        # call tools -- safely!
        for tool_call in tool_calls:
            tool = tools_by_name.get(tool_call.tool_name)
            print(f"DEBUG: Executing Tool: {tool_call.tool_name}")
            if not tool:
                current_reasoning.append(
                    ObservationReasoningStep(
                        observation=f"Tool {tool_call.tool_name} does not exist"
                    )
                )
                continue

            try:
                tool_output = tool(**tool_call.tool_kwargs)
                print(f"DEBUG: Tool Output: {tool_output}")
                sources.append(tool_output)
                current_reasoning.append(
                    ObservationReasoningStep(observation=tool_output.content)
                )
            except Exception as e:
                current_reasoning.append(
                    ObservationReasoningStep(
                        observation=f"Error calling tool {tool.metadata.get_name()}: {e}"
                    )
                )
            try:
                
                tool_outputs = await self.ctx.store.get("tool_outputs", default={})
                tool_outputs[tool_call.tool_name] = tool_output.raw_output
                await self.ctx.store.set("tool_outputs", tool_outputs)
        
                # if tool_call.tool_name in self.broadcast_tool_result:
                    # self.ctx.write_event_to_stream(
                    #     ToolCallResultWorkflowEvent(
                    #         tool_call_id=tool_call.tool_id,
                    #         tool_name=tool_call.tool_name,
                    #         # tool_kwargs=tool_call.tool_kwargs,
                    #         content=tool_output.content,
                    #         message_id=str(uuid.uuid4()),
                    #         role="tool",
                    #     )
                    # )
            except Exception as e:
                print(f"DEBUG: Error writing tool call result to stream: {e}")

        # save new state in context
        await ctx.store.set("sources", sources)
        await ctx.store.set("current_reasoning", current_reasoning)

        # prep the next iteraiton
        return PrepEvent()