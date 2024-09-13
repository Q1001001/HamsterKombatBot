from .common import os, json, logger, sleep, choices, SEP_LENGTH
from .client import Client
from .promoGame import PromoGame


class MainConfig():
    def __init__(self) -> None:
        self._mainConfName = "conf.json"
        self._promoConfName = "promoGames.json"
        self._promoGames: dict[str, object] = {}
        self._promoGamesCollect: list[object] = []
        self.loadConfig()
        logger.info(f"conf.json init".center(SEP_LENGTH, "-"))
        
    def __del__(self):
        logger.info(f"<red>conf.json destroyed</red>".center(SEP_LENGTH + 11, "-"))

    @logger.catch
    def loadConfig(self) -> bool:
        try:
            with open(self._mainConfName, "r") as configMainFile:
                self.configRAW = json.loads(configMainFile.read())
        except FileNotFoundError:
            logger.error(f"{self._mainConfName} config file not found!")
            return False
        except json.JSONDecodeError as er:
            logger.error(f"Wrong file {self._mainConfName}: {er}")
            return False

        options = self.configRAW.get("options")
        if not options:
            return False

        self.enableTaps = options.get("enableTaps", False)
        self.enableDailyTasks = options.get("enableDailyTasks", False)
        self.enableDailyCipher = options.get("enableDailyCipher", False)
        self.enableMiniGames = options.get("enableMiniGames", False)
        self.enableUpgrade = options.get("enableUpgrade", False)
        self.defaultDelay = options.get("defaultDelay", 3600)
        self.enablePromoGames = options.get("enablePromoGames", False)
        
        if self.enablePromoGames:
            try:
                with open(self._promoConfName, "r") as configPromoFile:
                    self.promoGamesConf = json.loads(configPromoFile.read())
            except FileNotFoundError:
                logger.error(f"{self._promoConfName} config file not found!")
                self.enablePromoGames = False
            except json.JSONDecodeError as er:
                logger.error(f"Wrong file {self._promoConfName}: {er}")
                self.enablePromoGames = False
        return True
    
    @property
    def clientsPromoGames(self):
        promoGames: list = []
        for client in self.clients:
            promoGames.extend([promoId for promoId in client.promoGames if client.getPromoGameByID(promoId).isActive])
        return list(set(promoGames))
    
    @property
    def promoGames(self) -> dict:
        if not hasattr(self, "_promoGames"):
            return {}
        return self._promoGames
    
    # @promoGames.setter
    # def promoGames(self, value):
    #     self._promoGames = value
    
    def initClients(self) -> None:
        clients = self.configRAW["clients"]
        self._clients = [Client(mainConfig=self, **clients[user]) for user in clients]
        logger.info("-" * SEP_LENGTH + "\n")
        
    def initPromoGames(self) -> None:
        for promoId in self.promoGamesConf:
            if promoId in self.clientsPromoGames and not promoId in self.promoGames:
                self.promoGames.update({
                    promoId: PromoGame(mainConfig=self, **self.promoGamesConf[promoId])
                })
            elif promoId in self.promoGames and not promoId in self.clientsPromoGames:
                del self.promoGames[promoId]
            elif promoId in self.promoGames:
                self.promoGames[promoId].updateConfig(**self.promoGamesConf[promoId])
        logger.info("<blue>" + "Promo games login timeout...".ljust(30, " ") + "\t~120 sec</blue>")
        sleep(120)
        logger.info("-" * SEP_LENGTH + "\n")
        
    def claimPromoCode(self, promoId: str, promoCode: str) -> None:
        clientsList = [client for client in self.clients \
                       if (not client.getPromoGameByID(promoId) is None) and client.getPromoGameByID(promoId).isActive]
        choices(clientsList, k=1)[0].claimPromoCode(promoId, promoCode)
        
    @property
    def lenClients(self) -> int:
        if not hasattr(self, "_clients"):
            return 0
        return len(self._clients)
        
    @property
    def clients(self) -> list:
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
            "defaultDelay": self.defaultDelay,
            "enableMiniGames": self.enableMiniGames
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
                self.clients.append(Client(mainConfig=self, **configData["clients"][clientName]))
        logger.info("-" * SEP_LENGTH + "\n\n")

    @logger.catch
    def minDelay(self) -> int:
        minDelay = self.defaultDelay
        dalayClients = list(filter(lambda client: client.minDelay > 0, self.clients))
        if dalayClients:
            minDelayClient = min(dalayClients, key=lambda clientDelay: clientDelay.minDelay)
            if minDelayClient.minDelay < minDelay:
                minDelay = minDelayClient.minDelay
        return minDelay