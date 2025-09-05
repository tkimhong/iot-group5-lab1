# IoT (001) Lab 1 (Group 5): ESP32 Temperature Monitor with Telegram Bot Control

This IoT project monitors temperature using an ESP32, DHT22 sensor, and a relay module. It sends Telegram alerts via a bot when temperature exceeds 30ºC and provides relay control via commands. The bot supports both private chats and group chats.

---

# Hardware Components

- ESP32 Dev Board (flashed MicroPython firmware)
- DHT22 temperature-humidity sensor
- 5V Relay module & power supply
- Some jumper wires

## Physical Wiring Photo

![Physical wiring](https://github.com/tkimhong/iot-group5-lab1/blob/main/assets/Lab1PhysicalWiringParts.jpg?raw=true)

---

# Software Configuration

### Prerequisites

1. ESP32 with MicroPython firmware installed
2. Telegram bot token from @BotFather
3. WiFi credentials

## Setup

1. **Create Telegram Bot**

- Message @BotFather on Telegram
- Create new bot with `/newbot`
- Save the bot token

2. **Configure credentials**

```py
WIFI_SSID = "YOUR-WIFI"
WIFI_PASSWORD = "YOUR-WIFI-PASSWORD"
BOT_TOKEN = "YOUR-BOT-TOKEN-HERE"
```

3. **Upload to ESP32**

- Copy `main.py` to ESP32 using IDE of your choice (Thonny was used here)
- Run the code
- Chat to the bot or add bot to group and chat from there
- Send `/start` to authorize the chat(s)

---

# Features

## Telegram Bot Commands

- `/start`: Show welcome message, and commands
- `/status`: Display current temperature, humidity, and relay state
- `/on` - Turn relay ON (stops alerts regardless of current temperature)
- `off` - Turn relay OFF

## Automatic Behavior

- **Normal Mode (T < 30ºC):** Silent monitoring
- **Alert Mode (T >= 30ºC):** Sends alerts every 5 seconds until `/on` received
- **Auto-OFF:** Relay turns OFF automatically when temperature drops below 30ºC

### Additional Features

- WiFi auto-reconnection
- Handles sensor read failures
- HTTP error handling (HTTP errors don't crash system)

---

## Flowchart

![Flowchart](https://github.com/tkimhong/iot-group5-lab1/blob/main/assets/Flowchart.jpg?raw=true)

---

# Demo

## Task 1: Sensor Reading

![Printing temp and humidity readings every 5 seconds in Thonny](https://github.com/tkimhong/iot-group5-lab1/blob/main/assets/Task1SerialOutput.png?raw=true)

_DHT22 readings printed every 5 seconds with 2 decimal places_

## Task 2: Telegram Send

![Telegram bot PM authorization](https://github.com/tkimhong/iot-group5-lab1/blob/main/assets/Task2BotAuthA.png?raw=true)
![Telegram bot group authorization](https://github.com/tkimhong/iot-group5-lab1/blob/main/assets/Task2BotAuthB.png?raw=true)

_Successful bot authorization and confirmation message_

## Task 3: Bot Commands

![Status Telegram bot command](https://github.com/tkimhong/iot-group5-lab1/blob/main/assets/Task3BotCommandsA.png?raw=true)
![Turn relay ON bot command](https://github.com/tkimhong/iot-group5-lab1/blob/main/assets/Task3BotCommandsB.png?raw=true)
![Turn relay OFF bot command](https://github.com/tkimhong/iot-group5-lab1/blob/main/assets/Task3BotCommandsC.png?raw=true)

_All three commands working: `/status`, `/on`, `/off`_

## Task 4: Temperature Logic

**Demo Video:**

[![Demo video](https://img.youtube.com/vi/PDgJL9Lm_MY/0.jpg)](https://www.youtube.com/watch?v=PDgJL9Lm_MY)

_The video shows_

- Normal operation (T < 30ºC)
- Temperature alerts when T >= 30ºC
- `/on` command suppresses relay alerts
- Auto-OFF when temperature drops below 30ºC

### Additional Screenshots

![Telegram temperature alerts](https://github.com/tkimhong/iot-group5-lab1/blob/main/assets/Additional1.png?raw=true)

_Temperature alerts_

![Telegram auto-OFF notification & /status](https://github.com/tkimhong/iot-group5-lab1/blob/main/assets/Additional2.png?raw=true)

_Auto-OFF notification (temperature < 30ºC)_

---

# Installation & Usage

1. **Clone the Repository**

```bash
git clone https://github.com/tkimhong/iot-group5-lab1
```

2. **Setup Your Hardware:** Follow wiring diagram and reference above
3. **Configure Code:** Update WiFi and Telegram credentials in `main.py`
4. **Upload & Run:** Copy `main.py` to ESP32 and execute
5. **Start Bot:** Send `/start` to bot in Telegram. Works for both private and group (add it)
