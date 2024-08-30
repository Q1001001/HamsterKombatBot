from .common import (request,
                    logger, 
                    time,
                    sleep,
                    randint,
                    choices,
                    uuid4,
                    SEP_LENGTH,
                    PROMO_LOGIN,
                    PROMO_REGISTER_EVENT,
                    PROMO_CREATE_CODE)
# from .mainConfig import MainConfig

class PromoGame():
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
            delayRetry = self.delayRetry + randint(0, 5)
            logger.info("Attempt to register an event " +
                        "{rC}".format(rC=retryCount).rjust(2, " ") + " / " +
                        "{rM}".format(rM=retryMax).rjust(2, " ") + " (retryDelay: ~" +
                        "{dR}".format(dR=delayRetry) + " sec)")
            sleep(delayRetry)
            self._updatePromoGameData(self.registerEvent())
            retryCount += 1

        if self.hasCode:
            logger.success(f"<green>Event registered successfully.</green>")
            self._updatePromoGameData(self.createCode())
            promoKey = self.promoCode
            if promoKey:
                logger.success(f"<green>{promoKey}</green>")
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
            eventId = str(uuid4())
        elif self.eventIdType == "timestamp":
            eventId = str(int(time() * 1000))
        elif self.eventIdType == "16x2str":
            eventId = f"{''.join(choices('abcdefghijklmnopqrstuvwxyz0123456789', k=16))}-{''.join(choices('abcdefghijklmnopqrstuvwxyz0123456789', k=16))}"
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
        clientID = f"{int(time() * 1000)}-{''.join(str(randint(0, 9)) for _ in range(19))}"
        if self.clientIdType == "32str":
            clientID = "".join(choices("abcdefghijklmnopqrstuvwxyz0123456789", k=32))
        elif self.clientIdType == "16str":
            clientID = "".join(choices("abcdefghijklmnopqrstuvwxyz0123456789", k=16))
        elif self.clientIdType == "5+32str":
            self.clientIdType == f"{''.join(choices('abcdefghijklmnopqrstuvwxyz0123456789', k=5))}_{''.join(choices('abcdefghijklmnopqrstuvwxyz0123456789', k=32))}"
        else:
            clientID = str(uuid4())

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