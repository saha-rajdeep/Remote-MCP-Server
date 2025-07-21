#!/usr/bin/env python3
"""
Simple MCP server using FastMCP to add two numbers - Containerized version.
"""

from fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("Simple Calculator Container")

@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together.
    
    Args:
        a: First number to addition
        b: Second number to addition
        
    Returns:
        The sum of a and b
    """
    result = a + b
    return result

if __name__ == "__main__":
    # Run with streamable-http transport for HTTP-based communication in containers
    # Note: FastMCP doesn't support transport_options parameter
    # Session timeout is handled by the underlying transport layer
    mcp.run(
        transport="streamable-http", 
        host="0.0.0.0", 
        port=8000
    )
