import asyncio
import os
import time
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import ToolMessage, AIMessage

load_dotenv()

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    api_key=os.getenv("GEMINI_API_KEY"),
)


def extract_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "") for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return str(content)


def analyze(messages, start, end):
    tools_used = []
    answer = None

    for m in messages:
        if isinstance(m, ToolMessage):
            tools_used.append(m.name)
        if isinstance(m, AIMessage) and m.content:
            answer = extract_text(m.content)

    return answer, tools_used, end - start


async def main():

    client = MultiServerMCPClient({
        "weather": {"transport": "http", "url": "http://localhost:8000/mcp"}
    })

    tools = await client.get_tools()

    agent = create_agent(
        model=model,
        tools=tools
    )

    print("\nWeather Agent\n")

    while True:
        q = input("Ask (ALERTS/FORECAST/Exit) for a particular city: ")
        if q.lower() == "exit":
            break

        start = time.perf_counter()
        response = await agent.ainvoke({"messages": [{"role": "user", "content": q}]})
        end = time.perf_counter()

        answer, tools_used, t = analyze(response["messages"], start, end)

        print("\nANSWER:\n", answer)
        print("\nTOOLS:", " -> ".join(tools_used))
        print(f"TIME: {t:.2f}s\n")


if __name__ == "__main__":
    asyncio.run(main())
