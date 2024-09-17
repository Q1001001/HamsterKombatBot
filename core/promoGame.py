from .common import (request,
                    logger, 
                    time,
                    sleep,
                    randint,
                    choices,
                    uuid4,
                    SEP_LENGTH,
                    STRING,
                    PROMO_LOGIN,
                    PROMO_REGISTER_EVENT,
                    PROMO_CREATE_CODE)
# from .mainConfig import MainConfig

class PromoGame():
    def __init__(self, mainConfig: object, **kwargs):
        self.promoId = kwargs["promoId"]
        self.title = kwargs["title"]
        self.userHeaders = {
            "Host": "api.gamepromo.io",
            "Origin": "",
            "Referer": "",
            "Content-Type": "application/json; charset=utf-8",
        }
        self.setInitParams(**kwargs)
        self.hasCode = False
        logger.info(f"{self.title}".ljust(30, " ") + f"\t<green>Activated</green>")
        
    def __del__(self):
        logger.info(f"{self.title}".ljust(30, " ") + f"\t<red>Removed</red>")
        
    def setInitParams(self, **kwargs) -> None:
        self.title = kwargs.get("title")
        self.appToken = kwargs.get("appToken")
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
        self._updatePromoGameData(self.loginClient())
    
    def updateConfig(self, **kwargs) -> None:
        self.setInitParams(**kwargs)

    @logger.catch
    def genPromoKey(self) -> str:
        logger.info(f"Generate {self.title} promo-key")
        promoKey = ""
        if hasattr(self, "clientToken"):
            self.userHeaders.update({
                "Authorization": f"Bearer {self.clientToken}"
            })
            retryCount = 1
            retryMax = int(self.delay / self.delayRetry)
            while retryCount <= retryMax and not self.hasCode and self.clientToken:
                delayRetry = self.delayRetry + randint(0, 5)
                logger.info("Attempt to register an event " +
                            "{rC}".format(rC=retryCount).rjust(2, " ") + " / " +
                            "{rM}".format(rM=retryMax).rjust(2, " ") + " (retryDelay: ~" +
                            "{dR}".format(dR=delayRetry) + " sec)")
                self._updatePromoGameData(self.registerEvent())
                if not self.hasCode:
                    sleep(delayRetry)
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
            eventId = f"{''.join(choices(STRING, k=16))}-{''.join(choices(STRING, k=16))}"
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

    def loginClient(self) -> dict:
        clientID = f"{int(time() * 1000)}-{''.join(str(randint(0, 9)) for _ in range(19))}"
        if self.clientIdType == "32str":
            clientID = "".join(choices(STRING, k=32))
        elif self.clientIdType == "16str":
            clientID = "".join(choices(STRING, k=16))
        elif self.clientIdType == "5+32str":
            self.clientIdType == f"{''.join(choices(STRING, k=5))}_{''.join(choices(STRING, k=32))}"
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
            err_message = data["error_message"]
            logger.error(err_message)
            
            if err_message == "Session expired":
                self.clientToken = ""
                logger.info("Attempt to update session...")
                self._updatePromoGameData(self.loginClient())
                
            if err_message == "Too many login attempts from single ip":
                logger.info("Attempt to relogin...".ljust(30, " ") + "\t~360 sec")
                sleep(360)
                self._updatePromoGameData(self.loginClient())
            return

        if "message" in data:
            logger.error(data["message"])
            return

        if "clientToken" in data:
            self.clientToken = data["clientToken"]

        if "hasCode" in data:
            self.hasCode = data["hasCode"]

        if "promoCode" in data:
            self.promoCode = data["promoCode"]