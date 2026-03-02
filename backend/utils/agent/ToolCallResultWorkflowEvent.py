from ag_ui.core.events import (
    EventType,
    ToolCallResultEvent,
)

from llama_index.core.workflow import Event


class ToolCallResultWorkflowEvent(ToolCallResultEvent, Event):
    type: EventType = EventType.TOOL_CALL_RESULT
