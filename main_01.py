import random
from fastmcp import FastMCP

mcp = FastMCP(name="demo_server")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


if __name__ == "__main__":
    mcp.run()
