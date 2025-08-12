import asyncio
from agent_sql_economic.agent import root_agent

async def main():
    """Asynchronously runs the agent and prints the response."""
    question = "What was the gdp and inflation for the US in 2025?"
    try:
        response = await root_agent.invoke({"question": question})
        print(response)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
