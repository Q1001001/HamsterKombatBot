from .common import (datetime,
                    b64decode, 
                    b64encode,
                    sha256,
                    randint,
                    request,
                    time,
                    json,
                    START_MINI_GAME,
                    CLAIM_DAILY_KEYS_MINIGAME)


class ClientMiniGame():
    # _client_mg_instances: dict[str, object] = {}
    
    # def __new__(cls, *args, **kwargs):
    #     if not args[0].id in cls._client_mg_instances:
    #         cls._client_mg_instances.update({
    #             args[0].id: {}
    #         })
    #     if not kwargs.get("id") in cls._client_mg_instances.get(args[0].id):
    #         cls._client_mg_instances.get(args[0].id).update({
    #             kwargs.get("id"): super().__new__(cls)
    #         })
    #     return cls._client_mg_instances.get(args[0].id).get(kwargs.get("id"))
    
    def __init__(self, parentObj: object, **kwargs):
        self.parentObj = parentObj
        self.id = kwargs.get("id")
        self.startDate = int(datetime.fromisoformat(kwargs.get("startDate").replace("Z", "+00:00")).timestamp())
        self.levelConfig = kwargs.get("levelConfig")
        self.youtubeUrl = kwargs.get("youtubeUrl")
        self.bonusKeys = kwargs.get("bonusKeys")
        self.maxPoints = kwargs.get("maxPoints", 0)
        self.isClaimed = kwargs.get("isClaimed", False)
        self.totalSecondsToNextAttempt = kwargs.get("totalSecondsToNextAttempt")
        self.remainSecondsToGuess = kwargs.get("remainSecondsToGuess")
        self.remainSeconds = kwargs.get("remainSeconds")
        self.remainSecondsToNextAttempt = kwargs.get("remainSecondsToNextAttempt")
        self.remainPoints = kwargs.get("remainPoints")
    
    @property
    def minDelay(self) -> int:
        if not self.isClaimed:
            if self.isCooldown:
                if self.remainSecondsToNextAttempt < self.parentObj.mainConfig.defaultDelay:
                    return self.remainSecondsToNextAttempt
            elif self.isStarted:
                if self.remainSecondsToGuess < self.parentObj.mainConfig.defaultDelay:
                    return self.remainSecondsToGuess - 30
        return self.parentObj.mainConfig.defaultDelay
        
    @property
    def Reward(self) -> float:
        if not hasattr(self, "_reward"):
            return 0
        return self._reward
    
    @Reward.setter
    def Reward(self, value):
        self._reward = value
    
    @property
    def Cipher(self) -> str:
        miniGameScore = 2 * (self.startDate + self.maxPoints)
        miniGameSignature = b64encode(sha256(f"R1cHard_AnA1{miniGameScore}G1ve_Me_y0u7_Pa55w0rD".encode()).digest()).decode()
        miniGameCipher = "|".join([
            f"0{''.join(str(randint(0, 9)) for _ in range(9))}",
            self.parentObj.id,
            self.id,
            str(miniGameScore),
            miniGameSignature
        ]).encode()
        return b64encode(miniGameCipher).decode()
    
    def miniGameStart(self) -> dict:
        userData = {
            "miniGameId": self.id
        }
        return self.updateState(request(url=START_MINI_GAME, headers=self.parentObj.userHeaders, data=userData))

                    
    def claimMiniGame(self) -> dict:
        userData = {
            "miniGameId": self.id,
            "cipher": self.Cipher
        }
        return self.updateState(request(url=CLAIM_DAILY_KEYS_MINIGAME, headers=self.parentObj.userHeaders, data=userData))
    
    @property
    def isStarted(self):
        if not self.isClaimed:
            try:
                if self.remainSecondsToGuess > 0 and \
                ((self.remainSecondsToGuess != self.remainSecondsToNextAttempt) or \
                    (self.remainSecondsToGuess == self.remainSecondsToNextAttempt == self.remainSeconds)):
                    return True
            except Exception:
                return False
        return False
    
    @property
    def isCooldown(self):
        if not self.isClaimed:
            try:
                if self.remainSecondsToNextAttempt > 0 and \
                self.remainSecondsToGuess != self.remainSecondsToNextAttempt:
                    return True
            except Exception:
                return False
        return False
    
    def updateState(self, data: dict) -> dict:
        if "clickerUser" in data:
            clickerUser = data["clickerUser"]
            if "miniGame" in clickerUser:
                miniGame = clickerUser["miniGame"].get(self.id)
                self.lastStartAt = int(datetime.fromisoformat(miniGame.get("lastStartAt").replace("Z", "+00:00")).timestamp())
                self.lastClaimAt = int(datetime.fromisoformat(miniGame.get("lastClaimAt").replace("Z", "+00:00")).timestamp())
                
        if "dailyKeysMiniGames" in data:
            if "id" in data["dailyKeysMiniGames"]:
                miniGameData = data["dailyKeysMiniGames"]
                self.remainSecondsToGuess = miniGameData["remainSecondsToGuess"]
                self.isClaimed = miniGameData["isClaimed"]
                self.Reward = data.get("bonus", 0)
        return data