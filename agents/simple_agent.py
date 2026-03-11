from core.tool_registry import ToolRegistry

class SimpleAgent:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def run(self, tool_name, *args, **kwargs):
        tool = self.registry.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        return tool(*args, **kwargs)
