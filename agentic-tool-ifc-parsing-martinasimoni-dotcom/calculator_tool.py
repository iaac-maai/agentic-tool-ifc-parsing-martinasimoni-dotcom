"""
Calculator tool for Gemini API.
"""

import google.generativeai as genai
from typing import Dict, Any


def calculate(operation: str, a: float, b: float) -> Dict[str, Any]:
    """
    Perform basic arithmetic operations.

    Args:
        operation: The operation to perform (add, subtract, multiply, divide)
        a: First number
        b: Second number

    Returns:
        Dictionary with the result or error message
    """
    operations = {
        'add': lambda x, y: x + y,
        'subtract': lambda x, y: x - y,
        'multiply': lambda x, y: x * y,
        'divide': lambda x, y: x / y if y != 0 else None
    }

    if operation not in operations:
        return {"error": f"Unknown operation: {operation}"}

    result = operations[operation](a, b)
    if result is None:
        return {"error": "Division by zero"}

    return {"result": result}


# Define the tool schema for Gemini
calculate_tool = genai.protos.Tool(
    function_declarations=[
        genai.protos.FunctionDeclaration(
            name="calculate",
            description="Perform basic arithmetic operations like add, subtract, multiply, or divide",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "operation": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="The operation to perform: add, subtract, multiply, or divide"
                    ),
                    "a": genai.protos.Schema(
                        type=genai.protos.Type.NUMBER,
                        description="First number"
                    ),
                    "b": genai.protos.Schema(
                        type=genai.protos.Type.NUMBER,
                        description="Second number"
                    )
                },
                required=["operation", "a", "b"]
            )
        )
    ]
)
