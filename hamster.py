import requests
import time
import random
import sys
import uuid
import os
import json
from datetime import datetime
from base64 import b64decode, b64encode
from loguru import logger
from fake_useragent import UserAgent
from hashlib import sha256


DOMAIN = "https://api.hamsterkombatgame.io"
PROMO_DOMAIN = "https://api.gamepromo.io/promo"
ACCOUNT_INFO = DOMAIN + "/auth/account-info"
BASE_URL = DOMAIN + "/clicker"
UPGRADES_FOR_BUY = BASE_URL + "/upgrades-for-buy"
BUY_UPGRADE = BASE_URL + "/buy-upgrade"
SYNC = BASE_URL + "/sync"
CONFIG = BASE_URL + "/config"
TAP = BASE_URL + "/tap"
BOOSTS_FOR_BUY = BASE_URL + "/boosts-for-buy"
BUY_BOOSTS = BASE_URL + "/buy-boost"
CLAIM_DAILY_CIPHER = BASE_URL + "/claim-daily-cipher"
CLAIM_DAILY_KEYS_MINIGAME = BASE_URL + "/claim-daily-keys-minigame"
START_MINI_GAME = BASE_URL + "/start-keys-minigame"
CHECK_TASKS = BASE_URL + "/check-task"
LIST_TASKS = BASE_URL + "/list-tasks"
CLAIM_DAILY_COMBO = BASE_URL + "/claim-daily-combo"
GET_PROMOS = BASE_URL + "/get-promos"
APPLY_PROMO = BASE_URL + "/apply-promo"
PROMO_LOGIN = PROMO_DOMAIN + "/login-client"
PROMO_REGISTER_EVENT = PROMO_DOMAIN + "/register-event"
PROMO_CREATE_CODE = PROMO_DOMAIN + "/create-code"

SEP_LENGTH = 75

logger.remove()
logger.add(sys.stdout, colorize=True, level="INFO",
           format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
           "<level>{level: <8}</level> | - <level>{message}</level>")
# logger.add("log.txt", level="INFO",
#            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
#            "<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}"
#            "</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
#            rotation="1 MB")
logger = logger.opt(colors=True)


class MainConfig():
    def __init__(self) -> None:
        self._filepath = os.path.join(os.path.dirname(__file__), "conf.json")
        self._promoGamesCollect = []
        self.loadConfig()
        logger.info(f"conf.json init".center(SEP_LENGTH, "-"))
        
    def __del__(self):
        logger.info(f"<red>conf.json destroyed</red>".center(SEP_LENGTH + 11, "-"))

    @logger.catch
    def loadConfig(self) -> bool:
        try:
            configFile = open(self._filepath, "r")
        except FileNotFoundError:
            logger.error(f"Config file not found!")
            return False

        configContent = configFile.read()
        configFile.close()

        try:
            self.configRAW = json.loads(configContent)
        except json.JSONDecodeError as er:
            logger.error(f"Wrong file {self._filepath}: {er}")
            return False
        
        if "promoGames" in self.configRAW:
            self.promoGames = self.configRAW["promoGames"]

        options = self.configRAW.get("options")
        if not options:
            return False

        self.enableTaps = options.get("enableTaps")
        self.enableDailyTasks = options.get("enableDailyTasks")
        self.enableDailyCipher = options.get("enableDailyCipher")
        self.enableUpgrade = options.get("enableUpgrade")
        self.defaultDelay = options.get("defaultDelay")
        self.enablePromoGames = options.get("enablePromoGames")
        return True
    
    @property
    def promoGames(self) -> dict:
        if not hasattr(self, "_promoGames"):
            return {}
        return self._promoGames
    
    @promoGames.setter
    def promoGames(self, value):
        self._promoGames = value
    
    def promoGamesCollect(self, client: object = None) -> dict:
        if client:
            if client.isAllKeysCollected:
                if client in self._promoGamesCollect:
                    self._promoGamesCollect.remove(client)
            elif not client in self._promoGamesCollect:
                self._promoGamesCollect.append(client)
        return self._promoGamesCollect
    
    def initClients(self) -> None:
        clients = self.configRAW["clients"]
        self._clients = [Client(mainConfig=self, **clients[user]) for user in clients]
        self._lenClients = len(self._clients)
        logger.info("-" * SEP_LENGTH + "\n")
        
    @property
    def lenClients(self):
        if not hasattr(self, "_lenClients"):
            return 0
        return self._lenClients
        
    @property
    def clients(self):
        if not hasattr(self, "_clients"):
            return []
        return self._clients

    @logger.catch
    def getHamster(self, index: int = 0) -> object:
        if index > self.lenClients:
            return None
        return self.clients[index]
    
    def getHamsterByName(self, hamsterName: str) -> object:
        if hamsterName:
            for client in self.clients:
                if client.name == hamsterName:
                    return client
        return None
    
    def updateConfig(self) -> None:
        logger.info("conf.json".ljust(30, " ") + "\tUpdate config")
        logger.info("-" * SEP_LENGTH)
        curMainConfig = {
            "enableTaps": self.enableTaps,
            "enableDailyTasks": self.enableDailyTasks,
            "enableDailyCipher": self.enableDailyCipher,
            "enableUpgrade": self.enableUpgrade,
            "enablePromoGames": self.enablePromoGames,
            "defaultDelay": self.defaultDelay
        }
        self.loadConfig()
        for confItem in curMainConfig:
            if curMainConfig.get(confItem) != self.__getattribute__(confItem):
                if isinstance(self.__getattribute__(confItem), bool):
                    if self.__getattribute__(confItem):
                        logger.info(f"{confItem}".ljust(30, " ") + "\t<green>True</green>")
                    else:
                        logger.info(f"{confItem}".ljust(30, " ") + "\t<red>False</red>")
                else:
                    logger.info(f"{confItem}".ljust(30, " ") + f"\t<green>{self.__getattribute__(confItem)}</green>")
                        
        configData = self.configRAW
        if self.clients:
            clientsNames = [client.name for client in self.clients]
            for clientName in clientsNames:
                if not clientName in configData["clients"]:
                    clientObj = self.getHamsterByName(clientName)
                    self.clients.remove(clientObj)

        for clientName in configData["clients"]:
            clientObj = self.getHamsterByName(clientName)
            if clientObj:
                clientObj.updateConfig(self, configData["clients"])
                logger.info(f"{clientName}".ljust(30, " ") + "\tUpdated")
            else:
                self.clients.append(Client(configData["promoGames"], self, **configData["clients"][clientName]))
        logger.info("-" * SEP_LENGTH + "\n\n")

    @logger.catch
    def minDelay(self) -> int:
        minDelay = self.defaultDelay
        minDelayClient = min(self.clients, key=lambda clientDelay: clientDelay.minDelay)
        if minDelayClient.minDelay < minDelay:
            minDelay = minDelayClient.minDelay
        return minDelay


class PromoGame(MainConfig):
    def __init__(self, hamsterName: str, promoGame: dict, mainConfig: object):
        self.isActive = False
        self.promoId = promoGame["promoId"]
        self.title = promoGame["title"]["en"]
        self.keysPerDay = promoGame["keysPerDay"]
        self.receiveKeysToday = 0
        self.hamsterName = hamsterName
        self.setInitParams(mainConfig)
        self.hasCode = False
        self.isLogin = False
        self.userHeaders = {
            "Host": "api.gamepromo.io",
            "Origin": "",
            "Referer": "",
            "Content-Type": "application/json; charset=utf-8",
        }
        logger.info(f"{self.title}".ljust(30, " ") + f"\t<green>added</green> to {self.hamsterName}")
        
    def __del__(self):
        logger.info(f"{self.title}".ljust(30, " ") + f"\t<red>removed</red> from {self.hamsterName}")
        
    def setInitParams(self, mainConfig: object) -> None:
        self.mainConfig = mainConfig
        if not self.promoId in self.mainConfig.promoGames:
            self.isActive = False
            return
        config = self.mainConfig.promoGames[self.promoId]
        self.name = config.get("name")
        self.appToken = config.get("appToken")
        self.userAgent = config.get("userAgent")
        self.x_unity_version = config.get("x-unity-version")
        self.clientOrigin = config.get("clientOrigin")
        self.clientIdType = config.get("clientIdType")
        self.clientVersion = config.get("clientVersion")
        self.eventIdType = config.get("eventIdType")
        self.eventOrigin = config.get("eventOrigin")
        self.eventType = config.get("eventType")
        self.delay = config.get("delay")
        self.delayRetry = config.get("delayRetry")
        self.isActive = True
        
    def updateState(self, state: dict) -> None:
        self.receiveKeysToday = state["receiveKeysToday"]
        if self.receiveKeysToday == self.keysPerDay:
            self.isActive = False
    
    def updateConfig(self, mainConfig) -> None:
        self.setInitParams(mainConfig)

    @logger.catch
    def genPromoKey(self) -> str:
        logger.info(f"Generate {self.name} promo-key")
        promoKey = ""
        if not self.isLogin:
            self._updatePromoGameData(self.loginClien())
        self.userHeaders.update({
            "Authorization": f"Bearer {self.clientToken}"
        })
        retryCount = 1
        retryMax = int(self.delay / self.delayRetry)
        while retryCount <= retryMax and not self.hasCode:
            delayRetry = self.delayRetry + random.randint(0, 5)
            logger.info("Attempt to register an event " +
                        "{rC}".format(rC=retryCount).rjust(2, " ") + " / " +
                        "{rM}".format(rM=retryMax).rjust(2, " ") + " (retryDelay: ~" +
                        "{dR}".format(dR=delayRetry) + " sec)")
            time.sleep(delayRetry)
            self._updatePromoGameData(self.registerEvent())
            retryCount += 1

        if self.hasCode:
            logger.info(f"<green>Event registered successfully.</green>")
            self._updatePromoGameData(self.createCode())
            promoKey = self.promoCode
            if promoKey:
                logger.info(f"<green>{promoKey}</green>")
                self.hasCode = False
                self.promoCode = ""
        return promoKey

    def createCode(self) -> dict:
        userData = {
            "promoId": self.promoId
        }
        return request(url=PROMO_CREATE_CODE, headers=self.userHeaders, data=userData)

    def registerEvent(self) -> dict:
        eventId = self.eventIdType
        if self.eventIdType == "uuid":
            eventId = str(uuid.uuid4())
        elif self.eventIdType == "timestamp":
            eventId = str(int(time.time() * 1000))
        userData = {
            "promoId": self.promoId,
            "eventId": eventId,
            "eventOrigin": self.eventOrigin
        }
        if self.eventType:
            userData.update({
                "eventType": self.eventType
            })
        return request(url=PROMO_REGISTER_EVENT, headers=self.userHeaders, data=userData)

    def loginClien(self) -> dict:
        clientID = f"{int(time.time() * 1000)}-{''.join(str(random.randint(0, 9)) for _ in range(19))}"
        if self.clientIdType == "32str":
            clientID = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=32))
        elif self.clientIdType == "16str":
            clientID = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=16))
        elif self.clientIdType == "uuid":
            clientID = str(uuid.uuid4())

        userData = {
            "appToken": self.appToken,
            "clientId": clientID,
            "clientOrigin": self.clientOrigin
        }
        if self.clientVersion:
            userData.update({
                "clientVersion": self.clientVersion
            })
        if self.x_unity_version:
            self.userHeaders.update({
                "X-Unity-Version": self.x_unity_version
            })
        return request(url=PROMO_LOGIN, headers=self.userHeaders, data=userData)

    def _updatePromoGameData(self, data: dict) -> None:
        if "error_message" in data:
            logger.error(data["error_message"])
            return

        if "message" in data:
            logger.error(data["message"])
            return

        if "clientToken" in data:
            self.clientToken = data["clientToken"]
            self.isLogin = True

        if "hasCode" in data:
            self.hasCode = data["hasCode"]

        if "promoCode" in data:
            self.promoCode = data["promoCode"]


class Client():
    def __init__(self, mainConfig: object, **kwargs):
        self.name = kwargs.get("name")
        self._promoGamesObj = []
        self.isAllKeysCollected = False
        self.setInitValues(mainConfig=mainConfig, **kwargs)
        logger.info(f"{self.name}".ljust(30, " ") + f"\t<green>added</green>")

    def __del__(self):
        logger.info(f"{self.name}".ljust(30, " ") + f"\t<red>removed</red>")
        
    def setInitValues(self, mainConfig: object, **kwargs) -> None:
        self.token = kwargs.get("token")
        self.mainConfig = mainConfig
        self.limitCoinPrice = kwargs.get("limitCoinPrice")
        self.minBalance = kwargs.get("minBalance")
        self.excludeItems = []
        if kwargs.get("excludeItems"):
            self.excludeItems.extend(kwargs.get("excludeItems"))
        self.userHeaders = {
            "Authorization": self.token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._updateClientUserData(request(url=GET_PROMOS, headers=self.userHeaders))
        self.minDelay = 0
    
    @property
    def promoGamesObj(self):
        if not hasattr(self, "_promoGamesObj"):
            return []
        return self._promoGamesObj
    
    def updateConfig(self, mainConfig: object, clients: dict) -> None:
        clientData = clients[self.name]
        if clientData:
            self.setInitValues(mainConfig, **clientData)
            logger.info("-" * SEP_LENGTH)
    
    def getPromoGameByID(self, promoID: str) -> object:
        if self.promoGamesObj:
            for promoGame in self.promoGamesObj:
                if promoGame.promoId == promoID:
                    return promoGame
        return None

    @logger.catch
    def sync(self) -> None:
        logger.info(f"<b>{self.name}</b>")
        logger.info("-" * SEP_LENGTH)
        url_list = [
            SYNC,
            LIST_TASKS,
            CONFIG,
            UPGRADES_FOR_BUY,
            BOOSTS_FOR_BUY,
            GET_PROMOS
        ]
        for requestURL in url_list:
            resultData = request(url=requestURL, headers=self.userHeaders)
            self._updateClientUserData(resultData)

        if self.mainConfig.enableTaps:
            if self.availableTaps > self.maxTaps / 2:
                self._updateClientUserData(self.tap())
            if self.availableTaps < (self.maxTaps / self.earnPerTap) and self.isAvailableTapsBoost:
                self._updateClientUserData(self.boostTap())
                self._updateClientUserData(self.tap())

        if self.mainConfig.enableDailyCipher:
            logger.info("<b>Check daily ciphers...</b>")
            if self.morseGame:
                logger.info(f"{'Morse-Game'.ljust(30, ' ')}\tAlready claimed")
            elif self.morseCipher:
                self._updateClientUserData(self.dailyCipher())
                if self.morseGame:
                    logger.info((f"{'Morse-Game'.ljust(30, ' ')}\t<green>Claimed</green>"))

            if self.miniGame:
                logger.info(f"{'Mini-Game'.ljust(30, ' ')}\tAlready claimed ({self.totalKeys})")
            else:
                self._updateClientUserData(self.dailyKeysMiniGame())
                if self.miniGame:
                    logger.info(f"{'Mini-Game'.ljust(30, ' ')}\t<green>Claimed</green> ({self.totalKeys})")
            logger.info("-" * SEP_LENGTH)

        if self.mainConfig.enableDailyTasks:
            logger.info("<b>Check daily tasks...</b>")
            if self.isStreakDays:
                logger.info(f"{'streak_days'.ljust(30, ' ')}\tAlready claimed")
            else:
                self._updateClientUserData(self.streakDays())
                if self.isStreakDays:
                    logger.info(f"{'streak_days'.ljust(30, ' ')}\t<green>Claimed</green>")

            if self.combo:
                logger.info(f"{'dailyCombo'.ljust(30, ' ')}\tAlready claimed")
            elif len(self.comboUpgrades) < 3:
                logger.info(f"{'dailyCombo'.ljust(30, ' ')}\tIn progress")
            else:
                self._updateClientUserData(self.dailyCombo())
                if self.combo:
                    logger.info(f"{'dailyCombo'.ljust(30, ' ')}\t<green>Claimed</green>")
            logger.info("-" * SEP_LENGTH)

        if self.mainConfig.enablePromoGames:
            logger.info("<b>Promo-games state...</b>")
            for gameObj in self.promoGamesObj:
                logger.info("{promoName}".format(promoName=gameObj.title).ljust(30, " ") + "\t" +
                            "{rKD}".format(rKD=gameObj.receiveKeysToday) + " / " +
                            "{kPD}".format(kPD=gameObj.keysPerDay)
                            )
            logger.info("-" * SEP_LENGTH)

        if self.mainConfig.enableUpgrade:
            logger.info("<b>Check upgrades...</b>")
            for item in self.upgradesForBuy[:10]:
                if self._isUpgradable(item):
                    logger.info(f"{item.get('id').ljust(30, ' ')}\t" +
                                "{pPHD:,} / ".format(pPHD=item["profitPerHourDelta"]).replace(",", " ").rjust(10, " ") +
                                "{cardPrice:,} \t".format(cardPrice=item["price"]).replace(",", " ").rjust(13, " ") +
                                "{coinPrice:,.2f}".format(coinPrice=item['price'] / item['profitPerHourDelta']).replace(",", " ").rjust(12, " "))
                    self._updateClientUserData(self.buyUpgrade(item))
            logger.info("-" * SEP_LENGTH)

    def promoGameKeyGen(self) -> None:
        if self.mainConfig.enablePromoGames and self._isNeedPromoGamesKeyGen():
            logger.info(f"{self.name} - Generate promo keys...")
            logger.info("-" * SEP_LENGTH)
            self._updateClientUserData(request(url=GET_PROMOS, headers=self.userHeaders))
            for gameObj in self.promoGamesObj:
                promoKey = ""
                if self._isPromoActive(gameObj):
                    promoKey = gameObj.genPromoKey()
                    if promoKey:
                        if self._updateClientUserData(self.promoCode(promoKey=promoKey)):
                            logger.info("{promoName}".format(promoName=gameObj.title).ljust(30, " ") + "\t" +
                                        "<green>{rKD}</green> / ".format(rKD=gameObj.receiveKeysToday) +
                                        "{kPD}".format(kPD=gameObj.keysPerDay))
                    else:
                        logger.warning("{promoName}".format(promoName=gameObj.title).ljust(30, " ") + "\tUnable to get a key")
                    logger.info("-" * SEP_LENGTH + "\n")
    
    def _isNeedPromoGamesKeyGen(self) -> bool:
        for item in self.promoGamesObj:
            if self._isPromoActive(item):
                return True
        return False

    def promoCode(self, promoKey: str) -> dict:
        userData = {
            "promoCode": promoKey
        }
        return request(url=APPLY_PROMO, headers=self.userHeaders, data=userData)

    def buyUpgrade(self, item: dict) -> dict:
        userData = {
            "timestamp": int(time.time()),
            "upgradeId": item["id"]
        }
        return request(url=BUY_UPGRADE, headers=self.userHeaders, data=userData)

    def dailyCombo(self) -> dict:
        return request(url=CLAIM_DAILY_COMBO, headers=self.userHeaders)

    def streakDays(self) -> dict:
        userData = {
            "taskId": "streak_days"
        }
        return request(url=CHECK_TASKS, headers=self.userHeaders, data=userData)

    def dailyKeysMiniGame(self) -> dict:
        userData = {
            "miniGameId": "Candles"
        }
        request(url=START_MINI_GAME, headers=self.userHeaders, data=userData)
        score = str(int(time.time()))
        time.sleep(random.randint(15, 20))
        self.miniGameCipher = "|".join([
            f"0{''.join(str(random.randint(0, 9)) for _ in range(9))}",
            self.id,
            "Candles",
            score,
            b64encode(sha256(f"415t1ng{score}0ra1cum5h0t".encode()).digest()).decode()
        ]).encode()
        
        userData = {
            "miniGameId": "Candles",
            "cipher": b64encode(self.miniGameCipher).decode()
        }
        # "cipher": b64encode(f"0300000000|{self.id}".encode()).decode()
        return request(url=CLAIM_DAILY_KEYS_MINIGAME, headers=self.userHeaders, data=userData)

    def dailyCipher(self) -> dict:
        cipher = self.morseCipher[:3] + self.morseCipher[4:]
        userData = {
            "cipher": b64decode(cipher.encode()).decode('utf-8')
        }
        return request(url=CLAIM_DAILY_CIPHER, headers=self.userHeaders, data=userData)

    def tap(self) -> dict:
        userData = {
            "count": self.availableTaps,
            "availableTaps": self.availableTaps,
            "timestamp": int(time.time())
        }
        return request(url=TAP, headers=self.userHeaders, data=userData)

    def boostTap(self) -> dict:
        userData = {
            "boostId": "BoostFullAvailableTaps",
            "timestamp": int(time.time())
        }
        return request(url=BUY_BOOSTS, headers=self.userHeaders, data=userData)

    def _isUpgradable(self, item: dict) -> bool:
        if item["id"] in self.excludeItems:
            logger.info(f"{item['id'].ljust(30, ' ')}\t<red>Skipped by conditions</red>")
            return False
        if item.get("cooldownSeconds"):
            if item["cooldownSeconds"] > 0:
                logger.info(f"{str(item['id']).ljust(30, ' ')}\tSkipped by cooldown")
                return False
        if self.minBalance > 0 and (self.balanceCoins - item["price"]) < self.minBalance:
            logger.info(f"{item['id'].ljust(30, ' ')}\t<yellow>Skipped by minBalance</yellow>")
            return False
        if item["price"] > self.balanceCoins:
            logger.info(f"{item['id'].ljust(30, ' ')}\tSkipped by balance")
            return False
        if item["price"] / item["profitPerHourDelta"] > self.limitCoinPrice:
            logger.info(f"{item['id'].ljust(30, ' ')}\t<yellow>Skipped by limitCoinPrice</yellow>")
            return False
        return True

    def _isPromoActive(self, item: object) -> bool:
        if not item.isActive:
            return False
        if item.receiveKeysToday < item.keysPerDay:
            return True
        return False

    @logger.catch
    def _updateClientUserData(self, data: dict) -> bool:
        if "error_message" in data:
            logger.error(data["error_message"])
            return False

        if "clickerUser" in data:
            clickerUser = data["clickerUser"]
            self.id = clickerUser["id"]
            self.totalKeys = clickerUser["totalKeys"]
            self.balanceCoins = clickerUser["balanceCoins"]
            self.totalCoins = clickerUser["totalCoins"]
            self.level = clickerUser["level"]
            self.availableTaps = clickerUser["availableTaps"]
            self.earnPerTap = clickerUser["earnPerTap"]
            self.lastSyncUpdate = clickerUser["lastSyncUpdate"]
            self.earnPassivePerHour = clickerUser["earnPassivePerHour"]
            self.earnPassivePerSec = clickerUser["earnPassivePerSec"]
            self.maxTaps = clickerUser["maxTaps"]
            self.boosts = clickerUser["boosts"]

        if "tasks" in data:
            for task in data["tasks"]:
                if task["id"] == "streak_days":
                    self.isStreakDays = task["isCompleted"]

        if "dailyKeysMiniGames" in data:
            if "Candles" in data["dailyKeysMiniGames"]:
                self.miniGame = data["dailyKeysMiniGames"]["Candles"]["isClaimed"]
            else:
                self.miniGame = data["dailyKeysMiniGames"]["isClaimed"]

        if "dailyCipher" in data:
            self.morseGame = data["dailyCipher"]["isClaimed"]
            self.morseCipher = ""
            if not self.morseGame:
                self.morseCipher = data["dailyCipher"]["cipher"]

        if 'dailyCombo' in data:
            self.combo = data["dailyCombo"]["isClaimed"]
            self.comboUpgrades = data["dailyCombo"]["upgradeIds"]

        if "upgradesForBuy" in data:
            self.upgradesForBuy = []
            self.upgradesCooldown = []
            self.minDelay = 0
            for item in data["upgradesForBuy"]:
                if item["isAvailable"] and not item["isExpired"]:
                    if item["profitPerHourDelta"] > 0:
                        self.upgradesForBuy.append(item)
                    elif item["price"] == 0:
                        if item["maxLevel"] >= item["level"]:
                            item.update({
                                "profitPerHourDelta": 1,
                                "price": 1
                            })
                            self.upgradesForBuy.append(item)
            self.upgradesForBuy.sort(key=lambda coinPrice: coinPrice["profitPerHourDelta"] / coinPrice["price"], reverse=True)
            self.upgradesCooldown = list(filter(lambda cooldown: not cooldown.get("cooldownSeconds") is None, self.upgradesForBuy))
            self.upgradesCooldown = list(filter(lambda cooldown: cooldown.get("cooldownSeconds") > 0, self.upgradesCooldown))
            self.upgradesCooldown.sort(key=lambda cooldown: cooldown.get("cooldownSeconds"))
            if self.upgradesCooldown:
                self.minDelay = self.upgradesCooldown[0]["cooldownSeconds"]

        if "boostsForBuy" in data:
            self.isAvailableTapsBoost = False
            for item in data["boostsForBuy"]:
                if item["id"] == "BoostFullAvailableTaps":
                    if item["cooldownSeconds"] == 0:
                        self.isAvailableTapsBoost = True

        if "promos" in data:
            for promoGame in data["promos"]:
                gameObj = self.getPromoGameByID(promoGame["promoId"])
                if gameObj:
                    gameObj.updateConfig(self.mainConfig)
                else:
                    gameObj = PromoGame(self.name, promoGame, self.mainConfig)
                    self.promoGamesObj.append(gameObj)
            
            del_gameList = []
            gamesList = [game["promoId"] for game in data["promos"]]
            for gameObj in self.promoGamesObj:
                if not gameObj.promoId in gamesList:
                    del_gameList.append(gameObj.promoId)
            
            for promoId in del_gameList:
                self.promoGamesObj.remove(self.getPromoGameByID(gameObjId))
                
        if "states" in data:
            for promoState in data["states"]:
                gameObj = self.getPromoGameByID(promoState["promoId"])
                if gameObj:
                    gameObj.updateState(promoState)
            self.isAllKeysCollected = not self._isNeedPromoGamesKeyGen()
        
        if "promoState" in data:
            gameObj = self.getPromoGameByID(data["promoState"]["promoId"])
            if gameObj:
                gameObj.updateState(data["promoState"])
            self.isAllKeysCollected = not self._isNeedPromoGamesKeyGen()
            
        return True

    def status(self) -> None:
        logger.info("<b>Status...</b>")
        lenResult = len(str(round(self.balanceCoins, 2))) + (len(str(round(self.balanceCoins, 2))) - 4) // 3
        logger.info(f"{'limitCoinPrice'.ljust(30, ' ')}\t" +
                    f"{self.limitCoinPrice:,}".replace(",", " "))
        logger.info(f"{'AvailableTaps:'.ljust(30, ' ')}\t" +
                    f"{self.availableTaps:,} / {self.maxTaps:,}".replace(',', ' '))
        logger.info(f"{'Result balance:'.ljust(30, ' ')}\t" +
                    "{balance:,.2f}".format(balance=round(self.balanceCoins, 2)).replace(",", " ").rjust(lenResult, " ") +
                    f" (min: {round(self.minBalance, 2):,.2f})".replace(',', ' '))
        logger.info(f"{'Earn passive per hour/sec:'.ljust(30, ' ')}\t" +
                    "{ePPH:,.2f}".format(ePPH=round(self.earnPassivePerHour, 2)).replace(",", " ").rjust(lenResult, " ") +
                    f" / {round(self.earnPassivePerSec, 2):,.2f}".replace(',', ' '))
        logger.info("-" * SEP_LENGTH)

        if self.upgradesCooldown:
            logger.info("<b>Cooldown list:</b>")
            for item in self.upgradesCooldown:
                logger.info(f"{item['id'].ljust(30, ' ')}\t+" +
                            "{pPHD:,.2f}\t".format(pPHD=item['profitPerHourDelta']).replace(",", " ").rjust(12, " ") +
                            "{coinPrice:,.2f}\t".format(coinPrice=round(item['price']/item['profitPerHourDelta'], 2)).replace(",", " ").rjust(10, " ") +
                            f"{str(item.get('cooldownSeconds')).rjust(6, ' ')} sec")
            logger.info("-" * SEP_LENGTH)

        if self.upgradesForBuy:
            logger.info("<b>Priority upgrade list:</b>")
            for item in self.upgradesForBuy[:(10 + len(self.excludeItems))]:
                if not item["id"] in self.excludeItems:
                    logger.info(f"{item['id'].ljust(30, ' ')}\t+" +
                                "{pPHD:,.2f}\t".format(pPHD=item['profitPerHourDelta']).replace(",", " ").rjust(12, " ") +
                                "{coinPrice:,.2f}\t".format(coinPrice=round(item['price']/item['profitPerHourDelta'], 2)).replace(",", " ").rjust(10, " ") +
                                f"{str(item.get('cooldownSeconds')).rjust(6, ' ')} sec")
            logger.info("-" * SEP_LENGTH + "\n")
            

def request(method: str = "POST", url: str = "", headers: dict = None, data: dict = None) -> dict:
    userAgent = UserAgent().safari
    defaultHeaders = {
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Host": "api.hamsterkombatgame.io",
        "Origin": "https://hamsterkombatgame.io",
        "Referer": "https://hamsterkombatgame.io/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": userAgent,
    }
    if not headers is None:
        for key, value in headers.items():
            defaultHeaders[key] = value
    try:
        if method == "GET":
            response = requests.get(url, headers=defaultHeaders)
        elif method == "POST":
            response = requests.post(
                url, headers=defaultHeaders, data=json.dumps(data))
        elif method == "OPTIONS":
            response = requests.options(url, headers=defaultHeaders)
        else:
            err_msg = f"Invalid method: {method}"
            return {"error_message": err_msg}
        return response.json()
    except Exception as e:
        err_msg = f"Error: {e}"
        return {"error_message": err_msg}


def main():
    try:
        logger.info("-" * SEP_LENGTH)
        logger.info(" <b>Hamster Kombat Bot by Qx</b> ".center(SEP_LENGTH + 7, "-"))
        logger.info("-" * SEP_LENGTH + "\n")
        
        HamsterConfig = MainConfig()
        HamsterConfig.loadConfig()
        HamsterConfig.initClients()
        promoIndex = 0
        while True:
            isNeedKeyGen = False
            clientIndex = 0
            while clientIndex < HamsterConfig.lenClients:
                HamsterConfig.getHamster(clientIndex).sync()
                HamsterConfig.getHamster(clientIndex).status()
                HamsterConfig.promoGamesCollect(HamsterConfig.getHamster(clientIndex))
                clientIndex += 1
            minDelay = random.randint(1, 30)
            minDelay += HamsterConfig.minDelay()
            iterTime = time.time()

            remainsDelay = minDelay
            while time.time() + 900 < iterTime + minDelay and len(HamsterConfig.promoGamesCollect()) > 0:
                promoClient = HamsterConfig.getHamster(promoIndex)
                if promoClient in HamsterConfig.promoGamesCollect():
                    promoClient.promoGameKeyGen()
                    HamsterConfig.promoGamesCollect(promoClient)    
                promoIndex += 1
                if promoIndex >= HamsterConfig.lenClients:
                    promoIndex = 0
            remainsDelay = int((iterTime + minDelay) - time.time())
            if remainsDelay > 0:
                logger.info(f"Continue in {remainsDelay} sec ({datetime.fromtimestamp(
                    time.time() + remainsDelay).strftime("%d.%m.%Y, %H:%M:%S")})")
                logger.info("*" * SEP_LENGTH + "\n\n")
                time.sleep(remainsDelay)
            HamsterConfig.updateConfig()
    except KeyboardInterrupt:
        logger.info("Hamster Kombat Bot terminated")
        return

if __name__ == "__main__":
    main()
