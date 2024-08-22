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
        self.userAgent = UserAgent().safari
        self.loadConfig()

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

    def initClients(self) -> None:
        clients = self.configRAW["clients"]
        self.__clients = [Client(**clients[user]) for user in clients]
        self.lenClients = len(self.__clients)

    def getHamster(self, index: int = 0) -> object:
        if index > len(self.__clients):
            return None
        return self.__clients[index]

    @logger.catch
    def minDelay(self) -> int:
        minDelay = self.defaultDelay
        minDelayClient = min(
            self.__clients, key=lambda clientDelay: clientDelay.minDelay)
        if minDelayClient.minDelay < minDelay:
            minDelay = minDelayClient.minDelay
        return minDelay

    def _request(self, method: str = "POST", url: str = "", headers: dict = None, data: dict = None) -> dict:
        defaultHeaders = {
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Host": "api.hamsterkombatgame.io",
            "Origin": "https://hamsterkombatgame.io",
            "Referer": "https://hamsterkombatgame.io/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": self.userAgent,
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


class PromoGame(MainConfig):
    def __init__(self, **kwargs):
        super(PromoGame, self).__init__()
        self.name = kwargs.get("name")
        self.appToken = kwargs.get("appToken")
        self.promoId = kwargs.get("promoId")
        self.userAgent = kwargs.get("userAgent")
        self.x_unity_version = kwargs.get("x-unity-version")
        self.clientOrigin = kwargs.get("clientOrigin")
        self.clientIdType = kwargs.get("clientIdType")
        self.clientVersion = kwargs.get("clientVersion")
        self.eventIdType = kwargs.get("eventIdType")
        self.eventOrigin = kwargs.get("eventOrigin")
        self.eventType = kwargs.get("eventType")
        self.delay = kwargs.get("delay")
        self.delayRetry = kwargs.get("delayRetry")
        self.hasCode = False
        self.isLogin = False
        self.userHeaders = {
            "Host": "api.gamepromo.io",
            "Origin": "",
            "Referer": "",
            "Content-Type": "application/json; charset=utf-8",
        }

    @logger.catch
    def genPromoKey(self) -> str:
        logger.info(f"Generate promo-key for {self.name}")
        logger.info("-" * SEP_LENGTH)
        promoKey = ""
        if not self.isLogin:
            self._updatePromoGameData(self.loginClien())
        self.userHeaders.update({
            "Authorization": f"Bearer {self.clientToken}"
        })
        retryCount = 1
        retryMax = int(self.delay / self.delayRetry)
        while retryCount <= retryMax and not self.hasCode:
            logger.info("Attempt to register an event " +
                        "{rC}".format(rC=retryCount).rjust(2, " ") + " / " +
                        "{rM}".format(rM=retryMax).rjust(2, " ") + " (retryDelay: ~" +
                        "{dR}".format(dR=self.delayRetry) + " sec)")
            time.sleep(self.delayRetry + random.randint(1, 5))
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
        return self._request(url=PROMO_CREATE_CODE, headers=self.userHeaders, data=userData)

    def registerEvent(self) -> dict:
        eventId = self.eventIdType
        if self.eventIdType == "uuid":
            eventId = str(uuid.uuid4())
        userData = {
            "promoId": self.promoId,
            "eventId": eventId,
            "eventOrigin": self.eventOrigin
        }
        if self.eventType:
            userData.update({
                "eventType": self.eventType
            })
        return self._request(url=PROMO_REGISTER_EVENT, headers=self.userHeaders, data=userData)

    def loginClien(self) -> dict:
        clientID = f"{int(time.time() * 1000)}-{''.join(str(random.randint(0, 9)) for _ in range(19))}"
        if self.clientIdType == "32str":
            clientID = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=32))
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
        return self._request(url=PROMO_LOGIN, headers=self.userHeaders, data=userData)

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


class Client(MainConfig):
    def __init__(self, **kwargs):
        super(Client, self).__init__()
        self.name = kwargs.get("name")
        self.token = kwargs.get("token")
        self.limitCoinPrice = kwargs.get("limitCoinPrice")
        self.minBalance = kwargs.get("minBalance")
        self.__promoGames = [PromoGame(**self.configRAW["promoGames"][game])
                             for game in self.configRAW["promoGames"]]
        self.lenPromoGames = len(self.__promoGames)
        self.minDelay = 0
        self.excludeItems = []
        if kwargs.get("excludeItems"):
            self.excludeItems.extend(kwargs.get("excludeItems"))
        self.userHeaders = {
            "Authorization": self.token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

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
            resultData = self._request(
                url=requestURL, headers=self.userHeaders)
            self._updateClientUserData(resultData)

        if self.enableTaps:
            while self.availableTaps > self.maxTaps / 2:
                self._updateClientUserData(self.tap())
                if self.availableTaps < self.maxTaps / self.earnPerTap:
                    self._updateClientUserData(self.boostTap())

        if self.enableDailyCipher:
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

        if self.enableDailyTasks:
            logger.info("<b>Check daily tasks...</b>")
            if self.isStreakDays:
                logger.info(f"{'streak_days'.ljust(30, ' ')}\tAlready claimed")
            else:
                self._updateClientUserData(self.streakDays())
                if self.isStreakDays:
                    logger.info(f"{'streak_days'.ljust(
                        30, ' ')}\t<green>Claimed</green>")

            if self.combo:
                logger.info(f"{'dailyCombo'.ljust(30, ' ')}\tAlready claimed")
            elif len(self.comboUpgrades) < 3:
                logger.info(f"{'dailyCombo'.ljust(30, ' ')}\tIn progress")
            else:
                self._updateClientUserData(self.dailyCombo())
                if self.combo:
                    logger.info(f"{'dailyCombo'.ljust(30, ' ')}\t<green>Claimed</green>")
            logger.info("-" * SEP_LENGTH)

        if self.enablePromoGames:
            logger.info("<b>Promo-games state...</b>")
            for item in self.promoGames:
                promoGameState = self._getPromoGameState(item)
                logger.info("{promoName}".format(promoName=promoGameState["title"]).ljust(30, " ") + "\t" +
                            "{rKD}".format(rKD=promoGameState["receiveKeysToday"]) + " / " +
                            "{kPD}".format(kPD=promoGameState["keysPerDay"])
                            )
            logger.info("-" * SEP_LENGTH)

        if self.enableUpgrade:
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
        if self.enablePromoGames:
            logger.info(f"{self.name} - Generate promo keys...")
            logger.info("-" * SEP_LENGTH)
            for item in self.promoGames:
                self._updateClientUserData(self._request(
                    url=GET_PROMOS, headers=self.userHeaders))
                promoKey = ""
                promoGameState = self._getPromoGameState(item)
                if self._isPromoActive(promoGameState):
                    promoKey = self.getPromoGameKeyByID(item)
                    if promoKey:
                        if self._updateClientUserData(self.promoCode(promoKey=promoKey)):
                            logger.info("{promoName}".format(promoName=promoGameState["title"]).ljust(30, " ") + "\t" +
                                        "{rKD}".format(rKD=promoGameState["receiveKeysToday"]) + "<green> (+1)</green> / " +
                                        "{kPD}".format(kPD=promoGameState["keysPerDay"]) + "\n")
                    else:
                        logger.warning("{promoName}".format(promoName=promoGameState["title"]).ljust(30, " ") + "\tUnable to get a key\n")
                else:
                    logger.info("{promoName}".format(promoName=promoGameState["title"]).ljust(30, " ") + "\t" +
                                "{rKD}".format(rKD=promoGameState["receiveKeysToday"]) + " / " +
                                "{kPD}".format(kPD=promoGameState["keysPerDay"])
                                )
            logger.info("-" * SEP_LENGTH + "\n\n")
    
    def isNeedPromoGamesKeyGen(self) -> bool:
        for item in self.promoGames:
            if self._isPromoActive(self._getPromoGameState(item)):
                return True
        return False

    def getPromoGameKeyByID(self, promoId: str) -> str:
        for game in self.__promoGames:
            if game.promoId == promoId:
                return game.genPromoKey()
        return ""

    def promoCode(self, promoKey: str) -> dict:
        userData = {
            "promoCode": promoKey
        }
        return self._request(url=APPLY_PROMO, headers=self.userHeaders, data=userData)

    def buyUpgrade(self, item: dict) -> dict:
        userData = {
            "timestamp": int(time.time()),
            "upgradeId": item["id"]
        }
        return self._request(url=BUY_UPGRADE, headers=self.userHeaders, data=userData)

    def dailyCombo(self) -> dict:
        return self._request(url=CLAIM_DAILY_COMBO, headers=self.userHeaders)

    def streakDays(self) -> dict:
        userData = {
            "taskId": "streak_days"
        }
        return self._request(url=CHECK_TASKS, headers=self.userHeaders, data=userData)

    def dailyKeysMiniGame(self) -> dict:
        self._request(url=START_MINI_GAME, headers=self.userHeaders)
        time.sleep(random.randint(15, 20))
        userData = {
            "cipher": b64encode(f"0300000000|{self.id}".encode()).decode()
        }
        return self._request(url=CLAIM_DAILY_KEYS_MINIGAME, headers=self.userHeaders, data=userData)

    def dailyCipher(self) -> dict:
        cipher = self.morseCipher[:3] + self.morseCipher[4:]
        userData = {
            "cipher": b64decode(cipher.encode()).decode('utf-8')
        }
        return self._request(url=CLAIM_DAILY_CIPHER, headers=self.userHeaders, data=userData)

    def tap(self) -> dict:
        userData = {
            "count": self.availableTaps,
            "availableTaps": self.availableTaps,
            "timestamp": int(time.time())
        }
        return self._request(url=TAP, headers=self.userHeaders, data=userData)

    def boostTap(self) -> dict:
        userData = {
            "boostId": "BoostFullAvailableTaps",
            "timestamp": int(time.time())
        }
        return self._request(url=BOOSTS_FOR_BUY, headers=self.userHeaders, data=userData)

    def _getPromoGameState(self, promoId: str) -> dict:
        if not promoId in self.promoStates:
            promoGameState = {
                "title": self.promoGames[promoId]["title"]["en"],
                "receiveKeysToday": 0,
                "keysPerDay": self.promoGames[promoId]["keysPerDay"]
            }
        else:
            promoGameState = {
                "title": self.promoGames[promoId]["title"]["en"],
                "receiveKeysToday": self.promoStates[promoId]["receiveKeysToday"],
                "keysPerDay": self.promoGames[promoId]["keysPerDay"]
            }
        return promoGameState

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

    def _isPromoActive(self, item: dict) -> bool:
        if item["receiveKeysToday"] < item["keysPerDay"]:
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

        if "dailyKeysMiniGame" in data:
            self.miniGame = data["dailyKeysMiniGame"]["isClaimed"]

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
            self.promoGames = {}
            for gameId in data["promos"]:
                self.promoGames.update({
                    gameId["promoId"]: gameId
                })

        if "states" in data:
            self.promoStates = {}
            for state in data["states"]:
                self.promoStates.update({
                    state["promoId"]: state
                })
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


def main():
    try:
        logger.info("-" * SEP_LENGTH)
        logger.info(
            " <b>Hamster Kombat Bot by Qx</b> ".center(SEP_LENGTH + 7, "-"))
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
                if not isNeedKeyGen:
                    isNeedKeyGen = HamsterConfig.getHamster(clientIndex).isNeedPromoGamesKeyGen()
                clientIndex += 1
            minDelay = random.randint(1, 30)
            minDelay += HamsterConfig.minDelay()
            iterTime = time.time()
            logger.info(f"Continue in {minDelay} sec ({datetime.fromtimestamp(
                iterTime + minDelay).strftime("%d.%m.%Y, %H:%M:%S")})")
            logger.info("*" * SEP_LENGTH + "\n\n")

            remainsDelay = minDelay
            if isNeedKeyGen:
                while time.time() + 1800 < iterTime + minDelay:
                    HamsterConfig.getHamster(promoIndex).promoGameKeyGen()
                    promoIndex += 1
                    if promoIndex >= HamsterConfig.lenClients:
                        promoIndex = 0
                    remainsDelay = (iterTime + minDelay) - time.time()

            if remainsDelay > 0:
                time.sleep(remainsDelay)
    except KeyboardInterrupt:
        logger.info("Hamster Kombat Bot terminated")
        return

if __name__ == "__main__":
    main()
