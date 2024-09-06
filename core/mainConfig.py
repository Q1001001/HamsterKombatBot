from .common import logger, SEP_LENGTH
from .common import os, json
from .client import Client


class MainConfig():
    def __init__(self) -> None:
        self._filepath = "conf.json"
        self._promoGamesCollect: list[object] = []
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

        self.enableTaps = options.get("enableTaps", False)
        self.enableDailyTasks = options.get("enableDailyTasks", False)
        self.enableDailyCipher = options.get("enableDailyCipher", False)
        self.enableMiniGames = options.get("enableMiniGames", False)
        self.enableUpgrade = options.get("enableUpgrade", False)
        self.defaultDelay = options.get("defaultDelay", 3600)
        self.enablePromoGames = options.get("enablePromoGames", False)
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
        logger.info("-" * SEP_LENGTH + "\n")
        
    @property
    def lenClients(self):
        if not hasattr(self, "_clients"):
            return 0
        return len(self._clients)
        
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