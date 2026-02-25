import requests
import hashlib
import xml.etree.ElementTree as ET
import json
import time
import os
from dotenv import load_dotenv

# --- KONFIGURATION LADEN ---
# Lädt die Variablen aus der .env Datei
load_dotenv()

FRITZBOX_IP = os.getenv("FRITZ_IP")
USERNAME = os.getenv("FRITZ_USER")
PASSWORD = os.getenv("FRITZ_PASS")
FRITZBOX_URL = f"http://{FRITZBOX_IP}"

# Prüfen, ob Passwörter gefunden wurden
if not PASSWORD or not FRITZBOX_IP:
    print("❌ Fehler: Keine Zugangsdaten gefunden.")
    print("Bitte erstelle eine '.env' Datei mit FRITZ_IP, FRITZ_USER und FRITZ_PASS.")
    exit()

# ZIEL: Wir wollen rub_2 schalten
TARGET_RULE_ID = "rub_2"

def get_sid():
    session = requests.Session()
    try:
        response = session.get(f"{FRITZBOX_URL}/login_sid.lua")
    except:
        print(f"❌ Keine Verbindung zu {FRITZBOX_IP}.")
        return None, None
    
    root = ET.fromstring(response.text)
    sid = root.find("SID").text
    challenge = root.find("Challenge").text
    
    if sid != "0000000000000000": return sid, session

    chksum = f"{challenge}-{PASSWORD}"
    md5_hash = hashlib.md5(chksum.encode("utf-16le")).hexdigest()
    login_response = session.get(f"{FRITZBOX_URL}/login_sid.lua", params={"username": USERNAME, "response": f"{challenge}-{md5_hash}"})
    
    try:
        sid_element = ET.fromstring(login_response.text).find("SID")
        if sid_element is not None:
            sid = sid_element.text
        return (sid, session) if sid != "0000000000000000" else (None, None)
    except:
        return None, None

def get_rules_json(session, sid):
    url = f"{FRITZBOX_URL}/data.lua"
    payload = {"sid": sid, "page": "callRedi", "xhr": "1", "lang": "de"}
    try:
        resp = session.post(url, data=payload)
        data = json.loads(resp.text)
        return data.get("data", {}).get("rul_list", [])
    except:
        return []

def toggle_rule(session, sid, rule_id, current_state_bool):
    url = f"{FRITZBOX_URL}/data.lua"
    
    # Logik umkehren: Wenn AN (True) -> Sende "0", Wenn AUS (False) -> Sende "1"
    new_val = "0" if current_state_bool else "1"
    action_text = "AUSSCHALTEN" if current_state_bool else "EINSCHALTEN"
    
    payload = {
        "sid": sid,
        "page": "callRedi",
        "xhr": "1",
        "apply": "",        # Bestätigt die Änderung
        rule_id: new_val    # z.B. rub_2 = 1
    }
    
    print(f"⚙️  Ändere {rule_id}: {action_text} (Setze Wert auf {new_val})...")
    resp = session.post(url, data=payload)
    return resp.status_code == 200

# --- HAUPTPROGRAMM ---
sid, session = get_sid()

if sid:
    print(f"✅ Login erfolgreich (SID: {sid})")
    
    # 1. Aktuellen Status holen
    rules = get_rules_json(session, sid)
    target_rule = next((r for r in rules if r["uid"] == TARGET_RULE_ID), None)
    
    if target_rule:
        ist_zustand = target_rule['active']
        status_text = "🟢 AN" if ist_zustand else "⚪ AUS"
        print(f"\n🔍 Gefunden: {target_rule['from']} (ID: {TARGET_RULE_ID})")
        print(f"   Status aktuell: {status_text}")
        
        # 2. Umschalten
        success = toggle_rule(session, sid, TARGET_RULE_ID, ist_zustand)
        
        if success:
            # Kurze Pause, damit die FritzBox Zeit zum Speichern hat
            time.sleep(1) 
            
            # 3. Überprüfung
            print("📡 Prüfe neuen Status...")
            rules_new = get_rules_json(session, sid)
            target_new = next((r for r in rules_new if r["uid"] == TARGET_RULE_ID), None)
            
            if target_new:
                neu_zustand = target_new['active']
                neu_icon = "🟢 AN" if neu_zustand else "⚪ AUS"
                if neu_zustand != ist_zustand:
                    print(f"✅ Erfolg! Neuer Status: {neu_icon}")
                else:
                    print(f"⚠️  Status unverändert ({neu_icon}). Hat die Box den Befehl ignoriert?")
        else:
            print("❌ Fehler beim Senden des Befehls.")
            
    else:
        print(f"❌ Regel {TARGET_RULE_ID} nicht gefunden.")

    # Logout
    session.get(f"{FRITZBOX_URL}/login_sid.lua?logout=1&sid={sid}")
else:
    print("Login fehlgeschlagen. Prüfe Benutzername/Passwort in der .env Datei.")
