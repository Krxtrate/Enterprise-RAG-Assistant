from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AdCounty")

@mcp.tool()
def hello():
    return "hello"

if __name__ == "__main__":
    print("Starting MCP...")
    mcp.run()