import asyncio
from mcp.client.stdio import stdio_client
from mcp.client.stdio import StdioServerParameters


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=[
            "backend/ppt_service/Office-PowerPoint-MCP-Server/ppt_mcp_server.py"
        ],
        env={}
    )

    async with stdio_client(server_params) as (read, write):
        # 创建 session
        from mcp import ClientSession

        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()

            # 查看所有 tools
            tools = await session.list_tools()
            print(tools)

            # 调用 tool
            result = await session.call_tool(
                "create_presentation",
                {}
            )

            print(result)


asyncio.run(main())