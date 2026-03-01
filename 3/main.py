import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp
from dotenv import load_dotenv

load_dotenv()

INSTRUCTIONS = """
1) Získej dnešní kurz EUR->CZK (ideálně kurz pro 1 EUR).
2) Spočítej 125 * kurz přes calculator tool.
3) Vypiš výsledek do konzole.
"""

MCP_HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}

async def main():
    fx = MCPServerStreamableHttp({
        "url": "http://127.0.0.1:8011/mcp",
        "headers": MCP_HEADERS,
    })
    calc = MCPServerStreamableHttp({
        "url": "http://127.0.0.1:8012/mcp",
        "headers": MCP_HEADERS,
    })

    try:
        await fx.connect()
        await calc.connect()

        agent = Agent(
            name="Show FX Calc",
            instructions=INSTRUCTIONS,
            model="gpt-4.1-mini",
            mcp_servers=[fx, calc],
        )

        result = await Runner.run(
            agent,
            input="Přepočítej 125 EUR na CZK podle dnešního kurzu a vypiš ho do konzole.",
        )
        print(result.final_output)

    finally:
        try:
            await calc.cleanup()
        except Exception as e:
            print(f"Cleanup calc failed: {e!r}")

        try:
            await fx.cleanup()
        except Exception as e:
            print(f"Cleanup fx failed: {e!r}")

if __name__ == "__main__":
    asyncio.run(main())