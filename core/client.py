from .common import (logger, 
                    request,
                    time,
                    sleep, 
                    randint,
                    datetime,
                    json,
                    b64decode,
                    urllib,
                    LOGIN,
                    SEP_LENGTH,
                    CLIENT_LEVEL,
                    GET_PROMOS,
                    UPGRADES_FOR_BUY,
                    BUY_UPGRADE,
                    SYNC,
                    CONFIG,
                    TAP,
                    BOOSTS_FOR_BUY,
                    BUY_BOOSTS,
                    CLAIM_DAILY_CIPHER,
                    CHECK_TASKS,
                    LIST_TASKS,
                    CLAIM_DAILY_COMBO,
                    GET_PROMOS,
                    APPLY_PROMO)
from .clientPromoGame import ClientPromoGame
from .clientMiniGame import ClientMiniGame


class Client():
    def __init__(self, mainConfig: object, clientName: str, clientToken: str):
        self.mainConfig = mainConfig
        self.name = clientName
        self.token = clientToken
        self.setConfig(self.mainConfig)
        self.userHeaders = {
            "Authorization": self.token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.__promoGames: dict[str, dict] = {}
        self.__miniGames: dict[str, dict] = {}
        self.upgradesCooldown: list[dict] = []
        logger.info(f"{self.name}".ljust(30, " ") + f"\t<green>added</green>")

    def __del__(self):
        logger.info(f"{self.name}".ljust(30, " ") + f"\t<red>removed</red>")
    
    @classmethod
    @logger.catch
    def authByQueryId(cls, mainConfig: object, clientName: str, queryId: str) -> object:
        decodedQuery = urllib.parse.unquote(urllib.parse.unquote(queryId))
        tgWebAppData = decodedQuery.split("&tgWebAppVersion")[0]
        if "tgWebAppData=" in tgWebAppData:
            tgWebAppData = tgWebAppData.replace("tgWebAppData=", "")
        userObject = tgWebAppData.split("user=")[1].split("&")[0]
        encodedUserObject = urllib.parse.quote(userObject)
        tgWebAppData = tgWebAppData.replace(userObject, encodedUserObject)

        userData = {
                "initDataRaw": tgWebAppData,
                "fingerprint": {},
            }

        userHeaders = {
            "Access-Control-Request-Headers": "authorization",
            "Access-Control-Request-Method": "POST",
        }

        request(method="OPTIONS", url=LOGIN, headers=userHeaders, data=userData)

        userHeaders = {
            "Authorization": "",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        respData = request(url=LOGIN, headers=userHeaders, data=userData)
        if "authToken" in respData:
            clientToken = f"Bearer {respData['authToken']}"
            return cls(mainConfig=mainConfig, clientName=clientName, clientToken=clientToken)
        else:
            logger.error(f"{clientName}".ljust(30, " ") + f"\t<red>failed to get user token</red>")
            return
        
    def setConfig(self, mainConfig: object) -> None:
        configData = mainConfig.configRAW["clients"][self.name]
        self.limitCoinPrice = configData.get("limitCoinPrice")
        self.minBalance = configData.get("minBalance")
        self.excludeItems = configData.get("excludeItems", [])
        
    @property
    def minDelay(self) -> int:
        defaultDelay = self.mainConfig.defaultDelay
        if self.upgradesCooldown:
            if defaultDelay > self.upgradesCooldown[0]["cooldownSeconds"]:
                defaultDelay = self.upgradesCooldown[0]["cooldownSeconds"]
        miniGamesList = [self.getMiniGameByID(miniGameId).minDelay for miniGameId in self.miniGames \
            if (not self.getMiniGameByID(miniGameId) is None) and \
            (self.getMiniGameByID(miniGameId).isStarted or self.getMiniGameByID(miniGameId).isCooldown)]
        miniGamesList.sort()
        if miniGamesList:
            if defaultDelay > miniGamesList[0]:
                defaultDelay = miniGamesList[0]
        return defaultDelay

    @property
    def promoGames(self) -> dict:
        return self.__promoGames

    def getPromoGameByID(self, promoID: str) -> object:
        if promoID in self.promoGames:
            return self.promoGames.get(promoID, None)
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

        if hasattr(self, "lastSyncUpdate"):
            logger.info(f"Status as of {datetime.fromtimestamp(self.lastSyncUpdate).strftime('%d.%m.%Y, %H:%M:%S')}\n")
                
        if self.mainConfig.enableTaps:
            if self.availableTaps > self.maxTaps / 2:
                self._updateClientUserData(self.tap())
            if self.availableTaps < (self.maxTaps / self.earnPerTap) and self.isAvailableTapsBoost:
                self._updateClientUserData(self.boostTap())
                self._updateClientUserData(self.tap())

        if self.mainConfig.enableDailyCipher:
            logger.info("<b>Check daily cipher...</b>")
            if self.morseGame:
                logger.info(f"{'Morse-Game'.ljust(30, ' ')}\tAlready claimed")
            elif self.morseCipher:
                self._updateClientUserData(self.dailyCipher())
                if self.morseGame:
                    logger.success((f"{'Morse-Game'.ljust(30, ' ')}\t<green>Claimed</green>"))
            logger.info("-" * SEP_LENGTH)
        
        if self.mainConfig.enableMiniGames:
            logger.info("<b>Check daily miniGames...</b>")
            for gameId in self.miniGames:
                miniGameObj = self.getMiniGameByID(gameId)
                if miniGameObj:
                    if miniGameObj.isClaimed:
                        logger.info("{gameId}".format(gameId=gameId).ljust(30, " ") + "\t" +
                                    "Already claimed")
                    else:
                        if miniGameObj.isStarted:
                            self._updateClientUserData(miniGameObj.claimMiniGame())
                            if miniGameObj.isClaimed:
                                logger.success("{gameId}".format(gameId=miniGameObj.id).ljust(30, " ") + "\t" +
                                               "Claimed (+{reward:,})".format(reward=miniGameObj.Reward).replace(",", " "))
                        elif miniGameObj.isCooldown:
                            logger.info("{gameId}".format(gameId=miniGameObj.id).ljust(30, " ") + "\t" + 
                                        "<yellow>Game is on cooldown (delay: ~{miniGameDelay:.2f} sec)</yellow>".format(miniGameDelay=miniGameObj.remainSecondsToNextAttempt))
                        else:
                            miniGameObj.miniGameStart()
                            logger.info("{gameId}".format(gameId=miniGameObj.id).ljust(30, " ") + "\t" + 
                                        "<green>Game started (delay: ~{miniGameDelay:.2f} sec)</green>".format(miniGameDelay=miniGameObj.minDelay))
                            # self.minDelay = miniGameObj.minDelay
            logger.info("-" * SEP_LENGTH)

        if self.mainConfig.enableDailyTasks:
            logger.info("<b>Check daily tasks...</b>")
            if self.isStreakDays:
                logger.info(f"{'streak_days_special'.ljust(30, ' ')}\tAlready claimed")
            else:
                self._updateClientUserData(self.streakDays(taskId="streak_days_special"))
                if self.isStreakDays:
                    logger.success(f"{'streak_days_special'.ljust(30, ' ')}\t<green>Claimed</green>")

            if self.combo:
                logger.info(f"{'dailyCombo'.ljust(30, ' ')}\tAlready claimed")
            elif len(self.comboUpgrades) < 3:
                logger.info(f"{'dailyCombo'.ljust(30, ' ')}\tIn progress")
            else:
                self._updateClientUserData(self.dailyCombo())
                if self.combo:
                    logger.success(f"{'dailyCombo'.ljust(30, ' ')}\t<green>Claimed</green>")
            logger.info("-" * SEP_LENGTH)

        if self.mainConfig.enablePromoGames:
            logger.info("<b>Promo-games state...</b>")
            for gameId in self.promoGames:
                gameObj = self.getPromoGameByID(gameId)
                if gameObj:
                    logger.info("{promoName}".format(promoName=gameObj.title).ljust(30, " ") + "\t" +
                                "{rKD}".format(rKD=gameObj.receiveKeysToday) + " / " +
                                "{kPD}".format(kPD=gameObj.keysPerDay)
                                )
            logger.info("-" * SEP_LENGTH)

        if self.mainConfig.enableUpgrade:
            logger.info("<b>Check upgrades...</b>")
            upgradeList = list(filter(lambda upgradeItem: (upgradeItem['price'] / upgradeItem['profitPerHourDelta']) <= self.limitCoinPrice, self.upgradesForBuy))
            for item in upgradeList:
                if self._isUpgradable(item):
                    logger.info(f"{item.get('id').ljust(30, ' ')}\t" +
                                "{pPHD:,} / ".format(pPHD=item["profitPerHourDelta"]).replace(",", " ").rjust(10, " ") +
                                "{cardPrice:,} \t".format(cardPrice=item["price"]).replace(",", " ").rjust(13, " ") +
                                "{coinPrice:,.2f}".format(coinPrice=item['price'] / item['profitPerHourDelta']).replace(",", " ").rjust(12, " "))
                    self._updateClientUserData(self.buyUpgrade(item))
            logger.info("-" * SEP_LENGTH)
        
        logger.info("<b>Status...</b>")
        lenResult = len("{totalCoins:,.2f}".format(totalCoins=self.totalCoins).replace(",", " "))
        logger.info(f"{'limitCoinPrice:'.ljust(30, ' ')}\t" +
                    f"{self.limitCoinPrice:,}".replace(",", " "))
        logger.info(f"{'Level:'.ljust(30, ' ')}\t" + 
                    f"{CLIENT_LEVEL.get(self.level, 'Unknown level')}")
        logger.info("Total keys:".ljust(30, " ") + "\t" + 
                    "{totalKeys}".format(totalKeys=self.totalKeys))
        logger.info("Tickets:".ljust(30, " ") + "\t" + 
                    "{tickets}".format(tickets=self.balanceTickets))
        logger.info(f"{'AvailableTaps:'.ljust(30, ' ')}\t" +
                    f"{self.availableTaps:,} / {self.maxTaps:,}".replace(',', ' '))
        logger.info(f"{'Total coins:'.ljust(30, ' ')}\t" + 
                    "{totalCoins:,.2f}".format(totalCoins=self.totalCoins).replace(",", " ").rjust(lenResult, " "))
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
        
    def claimPromoCode(self, promoId: str, promoKey: str) -> None:
        self._updateClientUserData(self.promoCode(promoKey=promoKey))
        if self._promoReward.get("type", "keys") == "keys":
            logger.success("{name}".format(name=self.name).ljust(30, " ") + "\t" +
                        "<green>{rKD}</green> / ".format(rKD=self.promoGames.get(promoId).receiveKeysToday) +
                        "{kPD}".format(kPD=self.promoGames.get(promoId).keysPerDay))
        else:
            promoReward = self._promoReward["amount"]
            logger.success("{name}".format(name=self.name).ljust(30, " ") + "\t" +
                        "<green>+{promoReward:,}</green>".format(promoReward=promoReward).replace(",", " "))

    def promoCode(self, promoKey: str) -> dict:
        userData = {
            "promoCode": promoKey
        }
        return request(url=APPLY_PROMO, headers=self.userHeaders, data=userData)

    def buyUpgrade(self, item: dict) -> dict:
        userData = {
            "timestamp": int(time()),
            "upgradeId": item["id"]
        }
        return request(url=BUY_UPGRADE, headers=self.userHeaders, data=userData)

    def dailyCombo(self) -> dict:
        return request(url=CLAIM_DAILY_COMBO, headers=self.userHeaders)

    def streakDays(self, taskId) -> dict:
        userData = {
            "taskId": taskId
        }
        return request(url=CHECK_TASKS, headers=self.userHeaders, data=userData)

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
            "timestamp": int(time())
        }
        return request(url=TAP, headers=self.userHeaders, data=userData)

    def boostTap(self) -> dict:
        userData = {
            "boostId": "BoostFullAvailableTaps",
            "timestamp": int(time())
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
            logger.warning(f"{item['id'].ljust(30, ' ')}\t<yellow>Skipped by minBalance</yellow>")
            return False
        if item["price"] > self.balanceCoins:
            logger.info(f"{item['id'].ljust(30, ' ')}\tSkipped by balance")
            return False
        if item["price"] / item["profitPerHourDelta"] > self.limitCoinPrice:
            logger.warning(f"{item['id'].ljust(30, ' ')}\t<yellow>Skipped by limitCoinPrice</yellow>")
            return False
        return True
    
    @property
    def miniGames(self) -> dict:
        return self.__miniGames
    
    def getMiniGameByID(self, miniGameID: str) -> object:
        if miniGameID in self.miniGames:
            return self.miniGames.get(miniGameID, None)
        return None

    @logger.catch
    def _updateClientUserData(self, data: dict) -> bool:
        self._promoReward = {}
        if "error_message" in data:
            logger.error(data["error_message"])
            return False
        
        if "authToken" in data:
            self.token = f"Bearer {data['authToken']}"

        if "clickerUser" in data:
            clickerUser = data["clickerUser"]
            self.id = clickerUser["id"]
            self.totalKeys = clickerUser.get("totalKeys", 0)
            self.balanceCoins = clickerUser.get("balanceCoins", 0)
            self.totalCoins = clickerUser.get("totalCoins", 0)
            self.level = clickerUser["level"]
            self.availableTaps = clickerUser["availableTaps"]
            self.earnPerTap = clickerUser["earnPerTap"]
            self.lastSyncUpdate = clickerUser["lastSyncUpdate"]
            self.earnPassivePerHour = clickerUser["earnPassivePerHour"]
            self.earnPassivePerSec = clickerUser["earnPassivePerSec"]
            self.maxTaps = clickerUser["maxTaps"]
            self.boosts = clickerUser["boosts"]
            self.balanceTickets = clickerUser.get("balanceTickets", 0)

        if "tasks" in data:
            self.isStreakDays = False
            for task in data["tasks"]:
                if task["id"] == "streak_days_special":
                    self.isStreakDays = task["isCompleted"]
        
        if "task" in data:
            self.isStreakDays = False
            if data["task"]["id"] == "streak_days_special":
                self.isStreakDays = data["task"]["isCompleted"]

        if "dailyKeysMiniGames" in data:
            miniGameData = data["dailyKeysMiniGames"]
            if not "id" in miniGameData:
                for miniGameId in miniGameData:
                    self.miniGames.update({
                        miniGameId: ClientMiniGame(self, **miniGameData[miniGameId])
                        # miniGameId: self.miniGames.get(miniGameId, ClientMiniGame(self, **miniGameData[miniGameId]))
                    })

        if "dailyCipher" in data:
            self.morseGame = data["dailyCipher"]["isClaimed"]
            self.morseCipher = ""
            if not self.morseGame:
                self.morseCipher = data["dailyCipher"]["cipher"]

        if "dailyCombo" in data:
            self.combo = data["dailyCombo"]["isClaimed"]
            self.comboUpgrades = data["dailyCombo"]["upgradeIds"]

        if "upgradesForBuy" in data:
            self.upgradesForBuy = []
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
            self.upgradesForBuy.sort(key=lambda coinPrice: coinPrice["price"] / coinPrice["profitPerHourDelta"])
            self.upgradesCooldown = list(filter(lambda cooldown: not cooldown.get("cooldownSeconds") is None, self.upgradesForBuy))
            self.upgradesCooldown = list(filter(lambda cooldown: cooldown.get("cooldownSeconds") > 0, self.upgradesCooldown))
            self.upgradesCooldown.sort(key=lambda cooldown: cooldown.get("cooldownSeconds"))

        if "boostsForBuy" in data:
            self.isAvailableTapsBoost = False
            for item in data["boostsForBuy"]:
                if item["id"] == "BoostFullAvailableTaps":
                    if item["cooldownSeconds"] == 0:
                        self.isAvailableTapsBoost = True

        if "promos" in data:
            for promoGame in data["promos"]:
                self.promoGames.update({
                    promoGame["promoId"]: self.promoGames.get(promoGame["promoId"], ClientPromoGame(promoGame))
                })
                
        if "states" in data:
            for promoState in data["states"]:
                promoId = promoState["promoId"]
                self.promoGames.update({
                   promoId: self.getPromoGameByID(promoId).updateState(promoState)
                })
        
        if "promoState" in data:
            promoState = data["promoState"]
            promoId = promoState["promoId"]
            self.promoGames.update({
                   promoId: self.getPromoGameByID(promoId).updateState(promoState)
                })
            
        if "reward" in data:
            self._promoReward = data["reward"]
            
        return True