# Hamster Kombat Bot

Hamster Kombat auto farm bot. The developer is not responsible for any consequences of using this bot.

Use it at your own risk!
## Screenshots

![App Screenshot](https://github.com/user-attachments/assets/311b661f-12d6-463d-8399-a4b3528752ce)

## conf.json (rename def_conf.json -> conf.json)

#### General options

```text
"options": {
        "enableTaps": true,         // Auto taps if available taps > maxTaps / 2 + energy boost
        "enableDailyTasks": true,   // Auto StreakDays and Combo (combo reward is available only if all of the comboCards have been bought)
        "enableDailyCipher": true,  // Auto play Morse-game
        "enableMiniGames": false,   // Auto play MiniGames
        "enableUpgrade": true,      // Auto upgrade cards.
        "enablePromoGames": true,   // Auto promo keys gen and claim
        "defaultDelay": 3600        // MAX delay(sec) per check. Less then 1800 deactivate promoGames
    },
```

#### User account options

```text
  "clients": {
        "YOUR USER NAME": {
            "name": "",             // Your user name
            "token": "",            // Your tokent like "Bearer 123123..."
            "queryId": "",          // Your query id. You can use queryId auth if you don't have a token.
            "limitCoinPrice": 1000, // Limit of coin price to buy a card. coin price = card price / card profitPerHourDelta
            "minBalance": 0,        // Minimum Maintained Balance
            "excludeItems": []      // OPTIONAL! Cards id to exclude upgrade
        }
    }
```
**_NOTE:_**  "token" must be absent if you use queryId auth.

## Installation

### Mac OS / Linux

Clone repository

```txt
git clone https://github.com/Q1001001/HamsterKombatBot.git && cd HamsterKombatBot && mv def_conf.json conf.json
```

Create and activate virtual env

```txt
python3 -m venv .venv && source .venv/bin/activate && pip3 install -r requirements.txt
```

Make your account settings to the conf.json and run the script

```txt
python3 hamster.py
```

### Windows

1. To create virtual env and install the dependencies run 'install.bat'
2. Make your account settings to the 'conf.json'
3. Run 'hamster.bat'
