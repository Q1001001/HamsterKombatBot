from core.common import logger, SEP_LENGTH, randint, sleep, time, datetime
from core.mainConfig import MainConfig


def main():
    logger.info("-" * SEP_LENGTH)
    logger.info(" <b>Hamster Kombat Bot by Qx</b> ".center(SEP_LENGTH + 7, "-"))
    logger.info("-" * SEP_LENGTH + "\n")
    
    HamsterConfig = MainConfig()
    HamsterConfig.loadConfig()
    HamsterConfig.initClients()
    while True:
        try:
            clientIndex = 0
            while clientIndex < HamsterConfig.lenClients:
                HamsterConfig.getHamster(clientIndex).sync()
                clientIndex += 1
            minDelay = HamsterConfig.minDelay() + randint(1, 20)
            iterTime = time()
            if HamsterConfig.enablePromoGames:
                while time() + 900 < iterTime + minDelay and len(HamsterConfig.clientsPromoGames) > 0:
                    HamsterConfig.initPromoGames()
                    for clientPromoId in HamsterConfig.clientsPromoGames:
                        promoClient = HamsterConfig.promoGames.get(clientPromoId, None)
                        if promoClient:
                            promoKey = promoClient.genPromoKey()
                            if promoKey:
                                HamsterConfig.claimPromoCode(clientPromoId, promoKey)
                            else:
                                logger.warning("{promoName}".format(promoName=promoClient.title).ljust(30, " ") + 
                                               "\tUnable to get a promo code")
                            logger.info("-" * SEP_LENGTH + "\n")
                            
            remainsDelay = int((iterTime + minDelay) - time())
        except Exception as ex:
            logger.error(ex)
            remainsDelay = HamsterConfig.defaultDelay
            
        if remainsDelay > 0:
            logger.info(f"Continue in {remainsDelay} sec ({datetime.fromtimestamp(time() + remainsDelay).strftime('%d.%m.%Y, %H:%M:%S')})")
            logger.info("*" * SEP_LENGTH + "\n\n")
            sleep(remainsDelay)
        HamsterConfig.updateConfig()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Hamster Kombat Bot terminated")