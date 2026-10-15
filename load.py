import sys
import os
import tkinter as tk
from tkinter import ttk
import requests
import json
import random
from datetime import datetime, timezone
from config import config

# Storage registry keys & filenames
PLUGIN_NAME = "SWS Carrier Tracker"
WEBHOOK_SETTING = "DiscordCarrier_WebhookURL"
IMAGE_SETTING = "DiscordCarrier_ImageURL"
NAME_SETTING = "DiscordCarrier_CarrierName"
SERIAL_SETTING = "DiscordCarrier_CarrierSerial"
LOG_FILENAME = "carrier_location.json"

# Global variable to store plugin directory path
PLUGIN_DIR = ""

# Random announcement quotes
QUOTES = [
    "Please ensure your seatbelts are fastened, tray tables are secured and your seat is in the upright position.",
    "If you look out to the port side of the vessel, you'll see RAMity's ship bouncing off an Anaconda.",
    "Hey, Captain, what's this button do?",
    "Thank you for flying with Brewer Corp...we probably won't shoot you when you take off.",
    "Would the CMDR in seat 4B please stop changing the power priorities? The coffee machine is now offline.",
    "We will be travelling at ludicrous speed - please keep your arms and legs inside the vessel at all times.",
    "The Sidewinder Syndicate accepts no liability for any skill issues experienced by passengers on this flight.",
    "We have experienced a minor electrical issue. Thank you for your patience while we investigate why it's Richard's fault.",
    "Please see the safety booklet at the side of your seat. We know you won't read it.",
    "For refreshments, please visit the bar. If you work out how to actually get a drink, please let us know.",
    "PSA: it's not called lithobraking if it's on a carrier. In unrelated news, hangar 14 is offline for repairs."
]

def format_location(system_name, body_name):
    """Formats location without repeating the system name if body already contains it."""
    system = (system_name or "").strip()
    body = (body_name or "").strip()

    if not body:
        return system
    if not system:
        return body

    if body.lower().startswith(system.lower()):
        return body
    
    return f"{system} {body}"

def get_log_file_path():
    """Gets the full path to the carrier location log file."""
    if PLUGIN_DIR:
        return os.path.join(PLUGIN_DIR, LOG_FILENAME)
    return LOG_FILENAME

def save_carrier_location(location_str):
    """Writes the current/last known carrier location to a local log file."""
    if not location_str or not location_str.strip():
        return
    
    log_path = get_log_file_path()
    try:
        data = {
            "last_location": location_str.strip(),
            "updated_utc": datetime.now(timezone.utc).isoformat()
        }
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[{PLUGIN_NAME}] Failed to write location log: {e}", file=sys.stderr)

def load_carrier_location(default_val="Unknown System"):
    """Reads the last known carrier location from the local log file."""
    log_path = get_log_file_path()
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_location", default_val)
        except Exception as e:
            print(f"[{PLUGIN_NAME}] Failed to read location log: {e}", file=sys.stderr)
    return default_val

def plugin_start3(plugin_dir):
    """Initializes plugin tracking inside EDMC."""
    global PLUGIN_DIR
    PLUGIN_DIR = plugin_dir
    return PLUGIN_NAME

def get_clean_config(key, default_val):
    """Safely retrieves a configuration key, ensuring it never returns an empty string."""
    val = config.get_str(key)
    if val and val.strip():
        return val.strip()
    return default_val

def send_test_webhook():
    """Fires a test embed directly to Discord using the current saved values."""
    webhook_url = config.get_str(WEBHOOK_SETTING)
    
    carrier_name = get_clean_config(NAME_SETTING, "SWS Carrier")
    carrier_serial = get_clean_config(SERIAL_SETTING, "8008135")
    image_url = config.get_str(IMAGE_SETTING)
    
    if not webhook_url or not webhook_url.strip():
        return "Missing Webhook URL"

    payload = {
        "embeds": [{
            "title": f"🧪 Connection Test — {carrier_name} ({carrier_serial})",
            "description": "If you are reading this, your settings have been saved and the Discord bridge is active!",
            "color": 3066993,  # Green
            "fields": [
                {"name": "Status", "value": "Online & Listening", "inline": True},
                {"name": "Engine Bridge", "value": "EDMC Client UI v5", "inline": True}
            ],
            "key": "-u9W!jM6HD)c%vAEJ/8v_t",
            "footer": {"text": f"SWS Verification Link — {carrier_serial}"}
        }]
    }

    if image_url and image_url.strip():
        payload["embeds"][0]["image"] = {"url": image_url.strip()}
        
    try:
        response = requests.post(
            webhook_url.strip(),
            json=payload,
            headers={'User-Agent': 'EDMC-Carrier-Bridge'},
            timeout=5
        )
        response.raise_for_status()
        return "Success"
    except Exception as e:
        return f"Error: {str(e)}"

def open_settings_window():
    """Spawns an independent configuration window hosting all custom carrier parameters."""
    root = tk.Toplevel()
    root.title("SWS Carrier Tracker Settings")
    root.geometry("520x320")
    root.attributes("-topmost", True)
    
    main_frame = ttk.Frame(root, padding="15")
    main_frame.pack(fill=tk.BOTH, expand=True)
    main_frame.columnconfigure(1, weight=1)
    
    ttk.Label(main_frame, text="Carrier Name:").grid(row=0, column=0, sticky=tk.W, pady=6)
    name_var = tk.StringVar(value=config.get_str(NAME_SETTING) or "")
    name_entry = ttk.Entry(main_frame, textvariable=name_var, width=45)
    name_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=6)
    
    ttk.Label(main_frame, text="Carrier Serial (ID):").grid(row=1, column=0, sticky=tk.W, pady=6)
    serial_var = tk.StringVar(value=config.get_str(SERIAL_SETTING) or "")
    serial_entry = ttk.Entry(main_frame, textvariable=serial_var, width=45)
    serial_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=6)
    
    ttk.Label(main_frame, text="Discord Webhook URL:").grid(row=2, column=0, sticky=tk.W, pady=6)
    webhook_var = tk.StringVar(value=config.get_str(WEBHOOK_SETTING) or "")
    webhook_entry = ttk.Entry(main_frame, textvariable=webhook_var, width=45)
    webhook_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=6)
    
    ttk.Label(main_frame, text="Carrier Image URL:").grid(row=3, column=0, sticky=tk.W, pady=6)
    image_var = tk.StringVar(value=config.get_str(IMAGE_SETTING) or "")
    image_entry = ttk.Entry(main_frame, textvariable=image_var, width=45)
    image_entry.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=6)
    
    status_label = ttk.Label(main_frame, text="", font=("Helvetica", 9, "italic"))
    status_label.grid(row=6, column=0, columnspan=2, pady=5)

    def trigger_test():
        config.set(NAME_SETTING, name_var.get().strip())
        config.set(SERIAL_SETTING, serial_var.get().strip())
        config.set(WEBHOOK_SETTING, webhook_var.get().strip())
        config.set(IMAGE_SETTING, image_var.get().strip())
        
        result = send_test_webhook()
        if result == "Success":
            status_label.config(text="✨ Test alert dispatched successfully!", foreground="green")
        else:
            status_label.config(text=f"❌ {result}", foreground="red")

    def save_and_close():
        config.set(NAME_SETTING, name_var.get().strip())
        config.set(SERIAL_SETTING, serial_var.get().strip())
        config.set(WEBHOOK_SETTING, webhook_var.get().strip())
        config.set(IMAGE_SETTING, image_var.get().strip())
        root.destroy()
        
    test_btn = ttk.Button(main_frame, text="⚡ Send Test Alert", command=trigger_test)
    test_btn.grid(row=4, column=0, columnspan=2, pady=6, sticky=tk.EW)

    save_btn = ttk.Button(main_frame, text="Save & Close Settings", command=save_and_close)
    save_btn.grid(row=5, column=0, columnspan=2, pady=4, sticky=tk.EW)

def plugin_app(parent):
    """Injects the customized setup access button directly onto EDMC's dashboard UI."""
    frame = tk.Frame(parent)
    setup_button = tk.Button(
        frame, 
        text="⚙️ SWS Carrier Tracker Settings", 
        command=open_settings_window,
        bd=1,
        highlightthickness=1,
        highlightbackground="black",
        highlightcolor="black",
        relief="flat",
        padx=10,
        pady=4
    )
    setup_button.pack(padx=5, pady=5, fill=tk.X)
    return frame

def journal_entry(cmdr, is_beta, system, station, entry, state):
    """Monitors live logs, seamlessly pulling details from user variables as fallback."""
    webhook_url = config.get_str(WEBHOOK_SETTING)
    image_url = config.get_str(IMAGE_SETTING)
    
    event_type = entry.get('event')

    # Record completed carrier jump to log
    if event_type == 'CarrierJump':
        system_name = entry.get('StarSystem', system or '')
        body_name = entry.get('Body', '')
        location_str = format_location(system_name, body_name)
        if location_str:
            save_carrier_location(location_str)

    if not webhook_url or not webhook_url.strip():
        return

    carrier_name = get_clean_config(NAME_SETTING, "SWS Carrier")
    carrier_callsign = get_clean_config(SERIAL_SETTING, "8008135")

    payload = None

    if event_type == 'CarrierJumpRequest':
        target_system = entry.get('SystemName', 'Unknown System')
        body_name = entry.get('Body', '')
        destination_str = format_location(target_system, body_name)
        
        # 1. Read origin from local log file; fall back to active EDMC system if log is missing
        origin_location = load_carrier_location(default_val=system or "Unknown System")

        # 2. Update log file with new destination so the NEXT jump uses this as origin
        if destination_str:
            save_carrier_location(destination_str)

        # Format departure time and countdown
        departure_str = entry.get('DepartureTime')
        time_display = "Unknown"
        
        if departure_str:
            try:
                departure_time = datetime.fromisoformat(departure_str.replace('Z', '+00:00'))
                now_utc = datetime.now(timezone.utc)
                remaining_seconds = int((departure_time - now_utc).total_seconds())
                
                formatted_date = departure_time.strftime("%d/%m/%Y %H:%M UTC")
                
                if remaining_seconds > 0:
                    minutes, seconds = divmod(remaining_seconds, 60)
                    countdown = f"{minutes}m {seconds}s"
                else:
                    countdown = "Imminent"
                    
                time_display = f"{formatted_date} ({countdown})"
            except Exception:
                time_display = departure_str

        random_quote = random.choice(QUOTES)

        payload = {
            "embeds": [{
                "title": f"🚨 {carrier_name} ({carrier_callsign}) — Jump Scheduled!",
                "description": f"The hyperspace countdown sequence has been initiated. **All personnel lock your ships down.**\n\n*{random_quote}*",
                "color": 15105570,  # Warning Orange
                "fields": [
                    {"name": "Commanding Officer", "value": str(cmdr), "inline": True},
                    {"name": "Origin System", "value": str(origin_location), "inline": True},
                    {"name": "Destination System", "value": str(destination_str), "inline": True},
                    {"name": "Departure Time", "value": time_display, "inline": False}
                ],
                "key": "-u9W!jM6HD)c%vAEJ/8v_t",
                "entry": entry,
                "footer": {"text": f"SWS Automated Log Protocol — {carrier_callsign}"}
            }]
        }

    elif event_type == 'CarrierJumpCancelled':
        payload = {
            "embeds": [{
                "title": f"🛑 {carrier_name} ({carrier_callsign}) — Jump Aborted",
                "description": "The scheduled frame shift drive jump has been **CANCELLED** by command.",
                "color": 15158332,  # Aborted Red
                "fields": [
                    {"name": "Status Update", "value": "The carrier will remain at its current coordinates.", "inline": False}
                ],
                "key": "-u9W!jM6HD)c%vAEJ/8v_t",
                "entry": entry,
                "footer": {"text": f"SWS Automated Log Protocol — {carrier_callsign}"}
            }]
        }

    if payload:
        if image_url and image_url.strip():
            payload["embeds"][0]["image"] = {"url": image_url.strip()}
            
        try:
            response = requests.post(
                webhook_url.strip(),
                json=payload,
                headers={'User-Agent': 'EDMC-Carrier-Bridge'},
                timeout=5
            )
            response.raise_for_status()
        except Exception as e:
            print(f"[{PLUGIN_NAME}] Discord dispatch error: {e}", file=sys.stderr)