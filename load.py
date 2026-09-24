import sys
import tkinter as tk
from tkinter import ttk
import requests
import json
from config import config

# Storage registry keys
PLUGIN_NAME = "SWS Carrier Tracker"
WEBHOOK_SETTING = "DiscordCarrier_WebhookURL"
IMAGE_SETTING = "DiscordCarrier_ImageURL"
NAME_SETTING = "DiscordCarrier_CarrierName"
SERIAL_SETTING = "DiscordCarrier_CarrierSerial"

def plugin_start3(plugin_dir):
    """Initializes plugin tracking inside EDMC."""
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
    
    # Enforce safe default strings so Discord never receives an empty value
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
    
    # 1. Carrier Name Entry Row
    ttk.Label(main_frame, text="Carrier Name:").grid(row=0, column=0, sticky=tk.W, pady=6)
    name_var = tk.StringVar(value=config.get_str(NAME_SETTING) or "")
    name_entry = ttk.Entry(main_frame, textvariable=name_var, width=45)
    name_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=6)
    
    # 2. Carrier Registration / Serial Row
    ttk.Label(main_frame, text="Carrier Serial (ID):").grid(row=1, column=0, sticky=tk.W, pady=6)
    serial_var = tk.StringVar(value=config.get_str(SERIAL_SETTING) or "")
    serial_entry = ttk.Entry(main_frame, textvariable=serial_var, width=45)
    serial_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=6)
    
    # 3. Webhook Input Row
    ttk.Label(main_frame, text="Discord Webhook URL:").grid(row=2, column=0, sticky=tk.W, pady=6)
    webhook_var = tk.StringVar(value=config.get_str(WEBHOOK_SETTING) or "")
    webhook_entry = ttk.Entry(main_frame, textvariable=webhook_var, width=45)
    webhook_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=6)
    
    # 4. Carrier Image URL Row
    ttk.Label(main_frame, text="Carrier Image URL:").grid(row=3, column=0, sticky=tk.W, pady=6)
    image_var = tk.StringVar(value=config.get_str(IMAGE_SETTING) or "")
    image_entry = ttk.Entry(main_frame, textvariable=image_var, width=45)
    image_entry.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=6)
    
    # Status feedback notice label
    status_label = ttk.Label(main_frame, text="", font=("Helvetica", 9, "italic"))
    status_label.grid(row=6, column=0, columnspan=2, pady=5)

    def trigger_test():
        # Temporarily cache text strings so the immediate connection test applies them
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
        
    # 5. Interactive Operation Buttons
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
    
    if not webhook_url or not webhook_url.strip():
        return

    # Check EDMC telemetry state; if absent, leverage saved parameters from configuration
    carrier_name = get_clean_config(NAME_SETTING, "SWS Carrier")
    carrier_callsign = get_clean_config(SERIAL_SETTING, "8008135")

    event_type = entry.get('event')
    payload = None

    if event_type == 'CarrierJumpRequest':
        target_system = entry.get('SystemName', 'Unknown System')
        payload = {
            "embeds": [{
                "title": f"🚨 {carrier_name} ({carrier_callsign}) — Jump Scheduled!",
                "description": "The hyperspace countdown sequence has been initiated. **All personnel lock your ships down.**",
                "color": 15105570,  # Warning Orange
                "fields": [
                    {"name": "Commanding Officer", "value": str(cmdr), "inline": True},
                    {"name": "Destination System", "value": str(target_system), "inline": True},
                    {"name": "Time to Departure", "value": "15 Minutes (Lockdown in 10)", "inline": False}
                ],
                "key": "-u9W!jM6HD)c%vAEJ/8v_t",
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