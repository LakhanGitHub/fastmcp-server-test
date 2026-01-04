import random
from fastmcp import FastMCP

mcp = FastMCP(name="demo_server_math_tools")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

@mcp.tool
def subtract(a: int, b: int) -> int:
    """Subtract two integers."""
    return a - b

@mcp.tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers."""
    return a * b

@mcp.tool
def power(a: int, b: int) -> int:
    """Raise a to the power of b."""
    return a ** b

@mcp.tool
def remainder(a: int, b: int) -> int:
    """Return the remainder of a divided by b."""
    return a % b

if __name__ == "__main__":
    mcp.run()
