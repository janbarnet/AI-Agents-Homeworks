import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp
from dotenv import load_dotenv

load_dotenv()

INSTRUCTIONS = """
Jsi agent, který umí pracovat s těmito nástroji:

1) FX tool – zjistí kurz EUR -> CZK
2) Calculator tool – umí provádět matematické výpočty

Pracuj podle zadání uživatele a použij vhodný nástroj.
Pokud je potřeba výsledek výpočtu, použij calculator tool.
Vrať finální výsledek.
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
            name="FX Calc Agent",
            instructions=INSTRUCTIONS,
            model="gpt-4.1-mini",
            mcp_servers=[fx, calc],
        )

        # =========================
        # RUN 1 – zjisti kurz
        # =========================
        result1 = await Runner.run(
            agent,
            input="Zjisti dnešní kurz EUR na CZK pro 1 EUR. Vrať pouze číslo.",
        )

        rate = result1.final_output.strip()
        print("Kurz:", rate)

        # =========================
        # RUN 2 – spočítej částku
        # =========================
        result2 = await Runner.run(
            agent,
            input=f"Spočítej 125 * {rate} pomocí calculator tool.",
        )

        print("Výsledek:", result2.final_output)

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