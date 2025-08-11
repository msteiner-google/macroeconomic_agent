"""Main agent."""

from google.adk.agents import Agent

from agent_sql_economic import module

root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.5-flash",
    description=("Agent to answer questions about the time and weather in a city."),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city."
    ),
    tools=[],
)
