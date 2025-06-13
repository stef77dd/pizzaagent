from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("shop_connector")

NWS_API_BASE = "https://api.essen-bestellen.eu/menu?shopId=77"
USER_AGENT = "pizzaagent/1.0"

async def make_request(url: str) -> dict[str, Any] | None:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature:dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    url = f"{NWS_API_BASE}&state={state}"
    data = await make_request(url)

    if not data or "features" not in data:
        return "No alerts found or unable to fetch alerts."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n\n".join(alerts)

@mcp.tool()
async def get_menu() -> str:
    menu_data = await make_request(NWS_API_BASE)
    return menu_data

if __name__ == "__main__":
    mcp.run(transport="stdio")