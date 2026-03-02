import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp
from dotenv import load_dotenv

load_dotenv()

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

        # ==========================================================
        # RUN 1 — ZÍSKEJ KURZ
        # ==========================================================
        fx_agent = Agent(
            name="FX Agent",
            instructions="""
Získej dnešní kurz EUR->CZK (pro 1 EUR).
Vrať pouze číselnou hodnotu kurzu.
""",
            model="gpt-4.1-mini",
            mcp_servers=[fx],
        )

        fx_result = await Runner.run(
            fx_agent,
            input="Jaký je dnešní kurz EUR na CZK?",
        )

        rate = fx_result.final_output.strip()
        print(f"Zjištěný kurz: {rate}")

        # ==========================================================
        # RUN 2 — SPOČÍTEJ 125 * KURZ
        # ==========================================================
        calc_agent = Agent(
            name="Calc Agent",
            instructions="""
Použij calculator tool.
Vypočítej 125 * zadaný kurz.
Vrať pouze číselný výsledek.
""",
            model="gpt-4.1-mini",
            mcp_servers=[calc],
        )

        calc_result = await Runner.run(
            calc_agent,
            input=f"Spočítej 125 * {rate}",
        )

        print(f"125 EUR je {calc_result.final_output} CZK")

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