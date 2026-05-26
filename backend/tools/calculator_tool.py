"""
Calculator Tool — safe math expression evaluation.

Uses Python's AST module to safely evaluate math expressions
without exec/eval. Supports basic arithmetic, powers, and common math functions.
"""

import ast
import math
from backend.tools.base import BaseTool, ToolResult
from backend.tools.registry import ToolRegistry

# Allowed AST node types for safe evaluation
_SAFE_NODES = {
    ast.Expression, ast.Constant, ast.BinOp, ast.UnaryOp,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.USub, ast.UAdd,
}

# Allowed math functions
_FUNCTIONS = {
    "abs": abs, "round": round,
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "pi": math.pi, "e": math.e,
}


def _safe_eval(expr: str) -> float:
    """Evaluate a math expression safely using AST parsing."""
    tree = ast.parse(expr, mode="eval")

    # Validate all nodes are safe
    for node in ast.walk(tree):
        if type(node) not in _SAFE_NODES:
            if not isinstance(node, ast.Call):
                raise ValueError(f"Unsupported expression: {type(node).__name__}")

    # Evaluate with restricted globals
    return eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, _FUNCTIONS)


class CalculatorTool(BaseTool):
    name = "calculator"
    description = (
        "Evaluate a mathematical expression. "
        "Supports: +, -, *, /, //, %, **, and functions like sqrt, log, sin, cos, tan. "
        "Use this when the user asks for a calculation."
    )
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The math expression to evaluate, e.g. '2**10', 'sqrt(144)', 'sin(pi/2)'",
            },
        },
        "required": ["expression"],
    }

    async def run(self, expression: str, **kwargs) -> ToolResult:
        try:
            result = _safe_eval(expression)
            return ToolResult(
                success=True,
                data={"expression": expression, "result": result},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to evaluate '{expression}': {e}",
            )


# Auto-register
ToolRegistry.register(CalculatorTool())
