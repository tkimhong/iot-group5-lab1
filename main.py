import gc
import json
import time

import dht
import machine
import network
import urequests
from machine import Pin, reset

# Hardware configuration
sensor = dht.DHT22(machine.Pin(4))  # GPIO4 for DHT22
RELAY_PIN = 2
TEMP_THRESHOLD = 30.0  # Temperature threshold in Celsius
RELAY_ACTIVE_LOW = False

# Network configuration
SSID = "YOUR-WIFI-NAME"
PASSWORD = "YOUR-WIFI-PASSWORD"

# Telegram configuration
BOT_TOKEN = "YOUR-BOT-TOKEN-HERE"
ALLOWED_CHAT_IDS = set()  # Auto-learn first chat ID (works for both private and group chats)
GROUP_MODE = True  # Set to True for enable for group chats, False for private only

# System settings
POLL_TIMEOUT_S = 5  # Reduced for more responsive checking
DEBUG = True

# Global variables
relay = Pin(RELAY_PIN, Pin.OUT)
last_temp = 0.0
last_humidity = 0.0
relay_state = False
alert_active = False

# API URL
API = "https://api.telegram.org/bot" + BOT_TOKEN


def log(*args):
    if DEBUG:
        print(*args)


def _urlencode(d):
    """URL encoding function"""
    parts = []
    for k, v in d.items():
        if isinstance(v, int):
            v = str(v)
        s = str(v)
        s = s.replace("%", "%25").replace(" ", "%20").replace("\n", "%0A")
        s = s.replace("&", "%26").replace("?", "%3F").replace("=", "%3D")
        parts.append(str(k) + "=" + s)
    return "&".join(parts)


def connect_wifi():
    """Connect to WiFi with auto-reconnection"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)

        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            print("Waiting for connection...")
            time.sleep(1)
            timeout -= 1

    if wlan.isconnected():
        print("✅ Connected to WiFi")
        print("IP address:", wlan.ifconfig()[0])
        return True
    else:
        print("❌ Failed to connect")
        return False


def relay_on():
    """Turn relay ON"""
    global relay_state
    relay.value(0 if RELAY_ACTIVE_LOW else 1)
    relay_state = True
    log("Relay turned ON")


def relay_off():
    """Turn relay OFF"""
    global relay_state
    relay.value(1 if RELAY_ACTIVE_LOW else 0)
    relay_state = False
    log("Relay turned OFF")


def relay_is_on():
    """Check if relay is ON"""
    return (relay.value() == 0) if RELAY_ACTIVE_LOW else (relay.value() == 1)


def read_sensor():
    """Read DHT22 sensor"""
    global last_temp, last_humidity

    try:
        sensor.measure()
        last_temp = sensor.temperature()
        last_humidity = sensor.humidity()

        # Print with 2 decimals every 5 seconds
        print("Temperature: {:.2f}°C".format(last_temp))
        print("Humidity: {:.2f}%".format(last_humidity))
        print("-" * 30)

        return True
    except OSError as e:
        print("Failed to read sensor:", e)
        return False


def send_message(chat_id, text):
    """Send Telegram msg"""
    try:
        url = API + "/sendMessage?" + _urlencode({"chat_id": chat_id, "text": text})
        r = urequests.get(url)
        response_text = r.text
        r.close()
        log("send_message OK to", chat_id, ":", text[:50] + "...")
        return True
    except Exception as e:
        print("send_message error:", e)
        return False
    finally:
        gc.collect()  # Clean up memory


def get_updates(offset=None, timeout=POLL_TIMEOUT_S):
    """Get updates from the bot"""
    qs = {"timeout": timeout}
    if offset is not None:
        qs["offset"] = offset
    url = API + "/getUpdates?" + _urlencode(qs)

    try:
        r = urequests.get(url)
        data = r.json()
        r.close()
        if not data.get("ok"):
            print("getUpdates not ok:", data)
            return []
        return data.get("result", [])
    except Exception as e:
        print("get_updates error:", e)
        return []
    finally:
        gc.collect()


def handle_temperature_logic():
    """temperature threshold logic"""
    global alert_active, relay_state

    if last_temp >= TEMP_THRESHOLD:
        # Temperature is above threshold
        if not relay_state:
            # Relay is OFF, send alert
            return "alert"
        else:
            # Relay is ON, stop alerts
            alert_active = False
            return "controlled"
    else:
        # Temperature is below threshold
        if relay_state:
            # Auto turn off relay
            relay_off()
            alert_active = False
            return "auto_off"
        else:
            alert_active = False
            return "normal"


def handle_cmd(chat_id, text, message_info=None):
    """Telegram commands"""
    global alert_active

    text = (text or "").strip()

    # For group chats, commands should start with / or mention the bot
    if GROUP_MODE and chat_id < 0:  # Negative chat_id indicates group
        # In groups, only respond to commands that start with /
        if not text.startswith('/'):
            return

        # Tip: You can also check for bot mentions
        # if '@your_bot_username' in text:
        #     # Handle mentions

    # (T3) commands
    if text == "/status" or text.startswith("/status@"):
        # Show current temperature, humidity, and relay state
        status_msg = "🌡️ Temperature: {:.2f}°C\n".format(last_temp)
        status_msg += "💧 Humidity: {:.2f}%\n".format(last_humidity)
        status_msg += "🔌 Relay: {}".format("ON" if relay_state else "OFF")

        # In groups, include name of person who requested the status
        if GROUP_MODE and chat_id < 0 and message_info:
            user_name = message_info.get("from", {}).get("first_name", "User")
            status_msg = "📊 Status for {}\n".format(user_name) + status_msg

        send_message(chat_id, status_msg)

    elif text == "/on" or text.startswith("/on@"):
        relay_on()
        alert_active = False  # Stop alerts when manually turned on
        response_msg = "🔌 Relay turned ON"

        # In groups, mention who turned it on
        if GROUP_MODE and chat_id < 0 and message_info:
            user_name = message_info.get("from", {}).get("first_name", "User")
            response_msg += " by {}".format(user_name)

        send_message(chat_id, response_msg)

    elif text == "/off" or text.startswith("/off@"):
        relay_off()
        response_msg = "🔌 Relay turned OFF"

        # In groups, mention who turned it off
        if GROUP_MODE and chat_id < 0 and message_info:
            user_name = message_info.get("from", {}).get("first_name", "User")
            response_msg += " by {}".format(user_name)

        send_message(chat_id, response_msg)

    elif text == "/start" or text.startswith("/start@"):
        welcome_msg = "🤖 ESP32 Temperature Monitor Bot\n\n"
        welcome_msg += "Commands:\n"
        welcome_msg += "/status - Get current readings\n"
        welcome_msg += "/on - Turn relay ON\n"
        welcome_msg += "/off - Turn relay OFF\n\n"
        welcome_msg += "🚨 Alert threshold: {:.1f}°C\n".format(TEMP_THRESHOLD)

        if GROUP_MODE and chat_id < 0:
            welcome_msg += "\n👥 Group mode: Commands work for all members"

        send_message(chat_id, welcome_msg)

    elif text.startswith('/'):
        send_message(chat_id, "❓ Unknown command. Send /start for help.")


def main():
    """Main program loop"""
    global ALLOWED_CHAT_IDS, alert_active

    print("🚀 Starting ESP32 Temperature Monitor...")

    # Initialize hardware
    relay_off()  # Start with relay OFF

    # Connect to WiFi
    if not connect_wifi():
        print("Cannot continue without WiFi")
        return

    # Initialize Telegram bot
    last_id = None
    old = get_updates(timeout=1)
    if old:
        last_id = old[-1]["update_id"]

    print("🤖 Bot running. Waiting for commands...")

    # Main loop
    loop_count = 0

    while True:
        try:
            # (T5) Auto-reconnect WiFi when dropped
            if not network.WLAN(network.STA_IF).isconnected():
                print("WiFi disconnected, reconnecting...")
                connect_wifi()

            # (T1) Read sensor every loop 5 seconds
            sensor_ok = read_sensor()

            if sensor_ok:
                # Handle temperature logic
                temp_state = handle_temperature_logic()

                # (T4) temperature alerts
                if temp_state == "alert":
                    alert_msg = "🚨 ALERT: Temperature {:.2f}°C ≥ {:.1f}°C\n".format(last_temp, TEMP_THRESHOLD)
                    alert_msg += "Please send /on to turn on cooling system"

                    # Send alert to all authorized chats
                    for chat_id in ALLOWED_CHAT_IDS:
                        send_message(chat_id, alert_msg)

                elif temp_state == "auto_off":
                    auto_off_msg = "✅ AUTO-OFF: Temperature dropped to {:.2f}°C\n".format(last_temp)
                    auto_off_msg += "Relay turned OFF automatically"

                    # Send auto-off notice to all authorized chats
                    for chat_id in ALLOWED_CHAT_IDS:
                        send_message(chat_id, auto_off_msg)

            # Process Telegram commands
            try:
                updates = get_updates(offset=(last_id + 1) if last_id is not None else None)
                for u in updates:
                    last_id = u["update_id"]
                    msg = u.get("message") or u.get("edited_message")
                    if not msg:
                        continue

                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "")

                    # Get chat type and user info for better group handling
                    chat_type = msg["chat"].get("type", "private")
                    user_info = msg.get("from", {})
                    user_name = user_info.get("first_name", "User")

                    log("From", chat_id, f"({chat_type})", "User:", user_name, "Message:", text)

                    # Auto-learn the first chat ID if none set (works for groups too)
                    if not ALLOWED_CHAT_IDS:
                        ALLOWED_CHAT_IDS = {chat_id}
                        log("Learned ALLOWED_CHAT_IDS =", ALLOWED_CHAT_IDS)

                        if chat_type == "group" or chat_type == "supergroup":
                            auth_msg = "✅ Group authorized! All members can control the relay.\n"
                            auth_msg += "Send /start to see available commands."
                        else:
                            auth_msg = "✅ Authorized. You can now control the relay."

                        send_message(chat_id, auth_msg)

                    if chat_id not in ALLOWED_CHAT_IDS:
                        send_message(chat_id, "❌ Not authorized.")
                        continue

                    # Handle the command with message info for group context
                    handle_cmd(chat_id, text, msg)

            except Exception as e:
                print("Command processing error:", e)

            # Wait 5 seconds before next loop (as required)
            time.sleep(5)
            loop_count += 1

            # Periodic status (every 60 loops = 5 minutes)
            if loop_count % 60 == 0:
                log("System running... Loop:", loop_count)

        except Exception as e:
            print("Main loop error:", e)
            time.sleep(5)


# Test message function (debugging purpose)
def test_telegram():
    """Test Telegram messaging - uncomment to test"""
    print("Testing Telegram messaging...")
    connect_wifi()

    # This will send to the first person who messages the bot
    print("Send any message to your bot first, then this will reply")

    updates = get_updates(timeout=5)
    if updates:
        chat_id = updates[-1]["message"]["chat"]["id"]
        send_message(chat_id, "🤖 Hello from ESP32! This is a test message.")
        print("Test message sent!")
    else:
        print("No messages found. Send a message to your bot first.")


# Uncomment the line below to test Telegram messaging (debug)
# test_telegram()

# Run main program
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
        relay_off()  # Turn off relay when stopping
    except Exception as e:
        print("Fatal error:", e)
        relay_off()  # Safety: turn off relay
        time.sleep(5)
        reset()
