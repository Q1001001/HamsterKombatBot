class ClientPromoGame():
    def __init__(self, promoGame: dict):
        self.promoId = promoGame["promoId"]
        self.title = promoGame["title"]["en"]
        self.keysPerDay = promoGame["keysPerDay"]
        self.receiveKeysToday = 0
    
    @property
    def isActive(self) -> bool:
        if self.receiveKeysToday >= self.keysPerDay:
            return False
        return True
        
    def updateState(self, state: dict) -> None:
        self.receiveKeysToday = state["receiveKeysToday"]
        return self