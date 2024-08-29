
# Hamster Kombat Bot
Hamster Kombat auto farm bot
## Screenshots
![App Screenshot](https://github.com/user-attachments/assets/311b661f-12d6-463d-8399-a4b3528752ce)
## conf.json (rename def_conf.json -> conf.json)

#### General options
```text
"options": {
        "enableTaps": true,         // Auto taps if available taps > maxTaps / 2 + energy boost
        "enableDailyTasks": true,   // Auto StreakDays and Combo (combo reward available if all comboCards have been bought)
        "enableDailyCipher": true,  // Auto play Morse-game and MiniGame
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
            "limitCoinPrice": 1000, // Limit of coin price to buy a card. coin price = card profitPerHourDelta / card price
            "minBalance": 0,        // Minimum Maintained Balance
            "excludeItems": []      // OPTIONAL! Cards id to exclude upgrade
        }
    }
```

## Installation

```txt
  git clone https://github.com/Q1001001/HamsterKombatBot.git
  cd HamsterKombatBot
  pip install -r requirements.txt
  python3 hamster.py
```
