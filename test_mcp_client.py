#!/usr/bin/env python3
"""
Fixed MCP client to test the remote EKS MCP server without strands dependency.
"""

import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async def test_remote_mcp():
    """Test the remote MCP server running in EKS."""
    
    print("🚀 Testing Remote MCP Server in EKS")
    print("=" * 50)
    
    # URL of the remote MCP server
    server_url = "<insert your loadbalancer URL>/mcp/"
    print(f"📡 Connecting to: {server_url}")
    
    try:
        # Create streamable HTTP client
        async with streamablehttp_client(server_url) as (read, write, get_session_id):
            print("✅ Connected to remote MCP server")
            print(f"📋 Session ID: {get_session_id()}")
            
            # Create client session
            async with ClientSession(read, write) as session:
                print("🔄 Initializing session...")
                
                # Initialize the session
                await session.initialize()
                print("✅ Session initialized successfully")
                
                # List available tools
                print("\n🛠️  Listing available tools...")
                tools_result = await session.list_tools()
                
                if tools_result.tools:
                    print(f"📋 Found {len(tools_result.tools)} tool(s):")
                    for tool in tools_result.tools:
                        print(f"   - {tool.name}: {tool.description}")
                        if hasattr(tool, 'inputSchema') and tool.inputSchema:
                            print(f"     Parameters: {tool.inputSchema.get('properties', {}).keys()}")
                else:
                    print("❌ No tools found")
                    return
                
                # Test the add_numbers tool
                print(f"\n🧮 Testing add_numbers tool...")
                test_case = {"a": 15.5, "b": 24.3}
                
                try:
                    print(f"\n   Testing: {test_case['a']} + {test_case['b']}")
                    result = await session.call_tool("add_numbers", test_case)
                    
                    if result.content:
                        for content in result.content:
                            if hasattr(content, 'text'):
                                print(f"   ✅ Result: {content.text}")
                            else:
                                print(f"   ✅ Result: {content}")
                    else:
                        print(f"   ⚠️  No content in result: {result}")
                        
                except Exception as tool_error:
                    print(f"   ❌ Tool call failed: {tool_error}")
                
                print(f"\n🎉 Remote MCP testing completed!")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Print more detailed error information
        import traceback
        print(f"   Full traceback:")
        traceback.print_exc()
        
        print(f"\n   This could be due to:")
        print(f"   - Network connectivity issues")
        print(f"   - MCP server not responding")
        print(f"   - Session management problems")
        print(f"   - Protocol version mismatch")

if __name__ == "__main__":
    asyncio.run(test_remote_mcp())
