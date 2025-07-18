import asyncio
import mcp_client
from pydantic_ai import Agent

async def get_pydantic_ai_agent():
    client = mcp_client.MCPClient()
    client.load_servers("mcp_config.json")
    tools = await client.start()
    return client, Agent(model='gpt-4o', tools=tools)

async def main():
    client, agent = await get_pydantic_ai_agent()
    while True:
        user_input = input("User: ")
        response = await agent.achat(user_input)
        print("AI:", response.content)

if __name__ == "__main__":
    asyncio.run(main())
