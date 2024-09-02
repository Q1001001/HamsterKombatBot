from .common import (logger, 
                    request,
                    time,
                    sleep, 
                    randint,
                    b64decode, 
                    b64encode,
                    sha256,
                    datetime,
                    SEP_LENGTH,
                    GET_PROMOS,
                    UPGRADES_FOR_BUY,
                    BUY_UPGRADE,
                    SYNC,
                    CONFIG,
                    TAP,
                    BOOSTS_FOR_BUY,
                    BUY_BOOSTS,
                    CLAIM_DAILY_CIPHER,
                    CLAIM_DAILY_KEYS_MINIGAME,
                    START_MINI_GAME,
                    CHECK_TASKS,
                    LIST_TASKS,
                    CLAIM_DAILY_COMBO,
                    GET_PROMOS,
                    APPLY_PROMO)
from .promoGame import PromoGame


class Client():
    def __init__(self, mainConfig: object, **kwargs):
        self.name = kwargs.get("name")
        self._promoGamesObj = []
        self._miniGames = {}
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
            for gameId in self._miniGames:
                if self._miniGames[gameId]["isClaimed"]:
                    logger.info("{gameId}".format(gameId=gameId).ljust(30, " ") + "\t" +
                                "Already claimed")
                else:
                    self._updateClientUserData(self.claimMiniGame(gameId))
                    if self._miniGames[gameId]["isClaimed"]:
                        logger.success("{gameId}".format(gameId=gameId).ljust(30, " ") + "\t" + 
                                       "Claimed ({reward:,})".format(reward=self._miniGames[gameId].get("Reward", 0)).replace(",", " "))
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
            upgradeList = list(filter(lambda upgradeItem: (upgradeItem['price'] / upgradeItem['profitPerHourDelta']) <= self.limitCoinPrice, self.upgradesForBuy))
            for item in upgradeList:
                if self._isUpgradable(item):
                    logger.success(f"{item.get('id').ljust(30, ' ')}\t" +
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
                            logger.success("{promoName}".format(promoName=gameObj.title).ljust(30, " ") + "\t" +
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
            "timestamp": int(time()),
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
    
    def _startMiniGame(self, miniGameId: str) -> None:
        userData = {
            "miniGameId": miniGameId
        }
        request(url=START_MINI_GAME, headers=self.userHeaders, data=userData)

    def claimMiniGame(self, miniGameId: str) -> None:
        self._startMiniGame(miniGameId)
        sleep(randint(15, 20))
        userData = {
            "miniGameId": miniGameId,
            "cipher": self._miniGames[miniGameId]["Cipher"]
        }
        return request(url=CLAIM_DAILY_KEYS_MINIGAME, headers=self.userHeaders, data=userData)

    def _getMiniGameCipher(self, game: dict) -> str:
        timeStart = int(datetime.fromisoformat(game["startDate"].replace("Z", "+00:00")).timestamp())
        miniGameScore = 2 * (timeStart + game.get("maxPoints", 0))
        miniGameSignature = b64encode(sha256(f"R1cHard_AnA1{miniGameScore}G1ve_Me_y0u7_Pa55w0rD".encode()).digest()).decode()
        miniGameCipher = "|".join([
            f"0{''.join(str(randint(0, 9)) for _ in range(9))}",
            self.id,
            game["id"],
            str(miniGameScore),
            miniGameSignature
        ]).encode()
        return b64encode(miniGameCipher).decode()

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
            miniGameData = data["dailyKeysMiniGames"]
            if "id" in miniGameData:
                self._miniGames.update({
                    miniGameData["id"]: {
                        "isClaimed": miniGameData["isClaimed"],
                        "Reward": data.get("bonus", 0)
                    }
                })
            else:
                for miniGame in miniGameData:
                    self._miniGames.update({
                        miniGame: {
                            "isClaimed": miniGameData[miniGame].get("isClaimed", False),
                            "Cipher":  self._getMiniGameCipher(miniGameData[miniGame]),
                            "Reward": 0
                        }
                    })

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
                gameObj = self.getPromoGameByID(gameObjId)
                if gameObj:
                    self.promoGamesObj.remove(gameObj)
                
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
        logger.info("Total keys".ljust(30, " ") + "\t" + 
                    "{totalKeys}".format(totalKeys=self.totalKeys))
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