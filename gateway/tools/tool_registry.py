import inspect
import json
import logging
from typing import Callable, Dict, Any, List, Optional

logger = logging.getLogger("cyberwar.tools.registry")

class ToolRegistry:
    """
    Centralized registry for all Kite SecOps agent tools.
    Manages OpenAI function schemas and async dispatch execution.
    """
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Decorator to register a tool function and its JSON schema.
        """
        def decorator(func: Callable):
            schema = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description.strip(),
                    "parameters": parameters or {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            self._tools[name] = func
            self._schemas[name] = schema
            logger.info(f"Registered tool: [{name}]")
            return func
        return decorator

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Returns the list of tool schemas for OpenAI/Gemini tool calls."""
        return list(self._schemas.values())

    async def execute(self, name: str, args: Dict[str, Any]) -> str:
        """
        Executes a registered tool by name with arguments.
        Safely formats results and catches errors.
        """
        if name not in self._tools:
            return json.dumps({
                "status": "error",
                "error": f"Tool '{name}' is not registered."
            })

        func = self._tools[name]
        try:
            logger.info(f"Dispatching tool [{name}] with args: {args}")
            if inspect.iscoroutinefunction(func):
                result = await func(**args)
            else:
                result = func(**args)

            if isinstance(result, str):
                return result
            return json.dumps(result, indent=2, default=str)
        except TypeError as te:
            logger.error(f"Argument mismatch for tool [{name}]: {te}")
            return json.dumps({
                "status": "error",
                "tool": name,
                "error": f"Invalid arguments provided: {str(te)}"
            })
        except Exception as e:
            logger.error(f"Error executing tool [{name}]: {e}", exc_info=True)
            return json.dumps({
                "status": "error",
                "tool": name,
                "error": str(e)
            })

# Global default registry instance
registry = ToolRegistry()
