import re
import json
import requests
import click
import logging
import os
from dotenv import load_dotenv

# --- KONFIGURATION LADEN ---
# Lädt die Variablen aus der .env Datei
load_dotenv()

def get_default_url():
    ip = os.getenv("FRITZ_IP")
    if ip:
        return f"http://{ip}"
    return "http://192.168.178.1"

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("fritzbox_user_reader")

@click.command()
@click.option(
    "--url",
    default=get_default_url(),
    show_default=True,
    help="Base URL of the Fritz!Box"
)
def main(url):
    """Extract active Fritz!Box usernames from the login page."""
    try:
        response = requests.get(f"{url}/login.lua", timeout=5)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        logger.error(f"Failed to fetch Fritz!Box page: {e}")
        return

    # Try to extract active users from JSON in HTML
    match = re.search(r'"activeUsers":\s*(\[.*?\])', html, re.DOTALL)
    if match:
        try:
            active_users = json.loads(match.group(1))
            usernames = [user["value"] for user in active_users]
            logger.info(f"Found usernames: {', '.join(usernames)}")
            return
        except Exception as e:
            logger.warning(f"Failed to parse activeUsers JSON: {e}")

    logger.warning("No usernames found with primary method. Trying fallback...")

    # Fallback: extract from data object
    match = re.search(r'const data = (\{.*?\});', html, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1).replace("\\/", "/"))
            usernames = [user["value"] for user in data.get("activeUsers", [])]
            if usernames:
                logger.info(f"Found usernames (fallback): {', '.join(usernames)}")
            else:
                logger.error("No usernames found in fallback data object.")
        except Exception as e:
            logger.error(f"Failed to parse fallback data object: {e}")
    else:
        logger.error("No usernames found. Please check the HTML manually.")

if __name__ == "__main__":
    main()