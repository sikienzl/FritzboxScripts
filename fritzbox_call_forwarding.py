import requests
import hashlib
import xml.etree.ElementTree as ET
import json
import time
import os
import click
import logging
from dotenv import load_dotenv

# --- LOAD CONFIGURATION ---
load_dotenv()

FRITZBOX_IP = os.getenv("FRITZ_IP")
USERNAME = os.getenv("FRITZ_USER")
PASSWORD = os.getenv("FRITZ_PASS")
FRITZBOX_URL = f"http://{FRITZBOX_IP}"
DEFAULT_RULE_ID = os.getenv("FRITZ_DEFAULT_RULE_ID")

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("fritzbox_call_forwarding")

def check_credentials():
    if not PASSWORD or not FRITZBOX_IP:
        logger.error("No credentials found. Please create a '.env' file with FRITZ_IP, FRITZ_USER and FRITZ_PASS.")
        exit(1)

def get_sid():
    session = requests.Session()
    try:
        response = session.get(f"{FRITZBOX_URL}/login_sid.lua")
    except Exception:
        logger.error(f"Cannot connect to {FRITZ_IP}.")
        return None, None

    root = ET.fromstring(response.text)
    sid = root.find("SID").text
    challenge = root.find("Challenge").text

    if sid != "0000000000000000":
        return sid, session

    chksum = f"{challenge}-{PASSWORD}"
    md5_hash = hashlib.md5(chksum.encode("utf-16le")).hexdigest()
    login_response = session.get(
        f"{FRITZBOX_URL}/login_sid.lua",
        params={"username": USERNAME, "response": f"{challenge}-{md5_hash}"}
    )

    try:
        sid_element = ET.fromstring(login_response.text).find("SID")
        if sid_element is not None:
            sid = sid_element.text
        return (sid, session) if sid != "0000000000000000" else (None, None)
    except Exception:
        return None, None

def get_rules_json(session, sid):
    url = f"{FRITZBOX_URL}/data.lua"
    payload = {"sid": sid, "page": "callRedi", "xhr": "1", "lang": "de"}
    try:
        resp = session.post(url, data=payload)
        data = json.loads(resp.text)
        return data.get("data", {}).get("rul_list", [])
    except Exception:
        return []

def toggle_rule(session, sid, rule_id, current_state_bool):
    url = f"{FRITZBOX_URL}/data.lua"
    new_val = "0" if current_state_bool else "1"
    action_text = "DISABLE" if current_state_bool else "ENABLE"

    payload = {
        "sid": sid,
        "page": "callRedi",
        "xhr": "1",
        "apply": "",
        rule_id: new_val
    }

    logger.info(f"Changing {rule_id}: {action_text} (Set value to {new_val})...")
    resp = session.post(url, data=payload)
    return resp.status_code == 200

@click.command()
@click.option(
    "--rule-id",
    default=DEFAULT_RULE_ID,
    help="ID of the call forwarding rule to toggle (default from .env: FRITZ_DEFAULT_RULE_ID)"
)
@click.option(
    "--list",
    is_flag=True,
    help="List all available call forwarding rules"
)
def main(rule_id, list):
    """Toggle a call forwarding rule or list all rules on your Fritz!Box."""
    check_credentials()
    sid, session = get_sid()

    if not sid:
        logger.error("Login failed. Check username/password in the .env file.")
        return

    logger.info(f"Login successful (SID: {sid})")
    rules = get_rules_json(session, sid)

    if list:
        if not rules:
            logger.warning("No call forwarding rules found.")
        else:
            logger.info("Available call forwarding rules:")
            for rule in rules:
                status = "ON" if rule.get('active') else "OFF"
                from_number = rule.get('from', '<unknown>')
                to_number = rule.get('to', '<unknown>')
                description = rule.get('descr', '')
                logger.info(
                    f"  ID: {rule.get('uid', '<no id>')}\n"
                    f"    From: {from_number}\n"
                    f"    To: {to_number}\n"
                    f"    Description: {description}\n"
                    f"    Status: {status}\n"
                )
        # Logout
        session.get(f"{FRITZBOX_URL}/login_sid.lua?logout=1&sid={sid}")
        return

    if not rule_id:
        logger.error("No rule ID specified. Use --rule-id to toggle a rule or --list to show all rules.")
        session.get(f"{FRITZBOX_URL}/login_sid.lua?logout=1&sid={sid}")
        return

    target_rule = next((r for r in rules if r["uid"] == rule_id), None)
    if target_rule:
        current_state = target_rule['active']
        status_text = "ON" if current_state else "OFF"
        logger.info(f"Found: {target_rule.get('from', '<unknown>')} (ID: {rule_id})")
        logger.info(f"Current status: {status_text}")

        # Toggle
        success = toggle_rule(session, sid, rule_id, current_state)

        if success:
            time.sleep(1)
            logger.info("Checking new status...")
            rules_new = get_rules_json(session, sid)
            target_new = next((r for r in rules_new if r["uid"] == rule_id), None)

            if target_new:
                new_state = target_new['active']
                new_icon = "ON" if new_state else "OFF"
                if new_state != current_state:
                    logger.info(f"Success! New status: {new_icon}")
                else:
                    logger.warning(f"Status unchanged ({new_icon}). Did the box ignore the command?")
        else:
            logger.error("Failed to send the command.")
    else:
        logger.error(f"Rule {rule_id} not found.")

    # Logout
    session.get(f"{FRITZBOX_URL}/login_sid.lua?logout=1&sid={sid}")

if __name__ == "__main__":
    main()
