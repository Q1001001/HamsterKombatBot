from core.common import logger, SEP_LENGTH, randint, sleep, time, datetime
from core.mainConfig import MainConfig


def main():
    try:
        logger.info("-" * SEP_LENGTH)
        logger.info(" <b>Hamster Kombat Bot by Qx</b> ".center(SEP_LENGTH + 7, "-"))
        logger.info("-" * SEP_LENGTH + "\n")
        
        HamsterConfig = MainConfig()
        HamsterConfig.loadConfig()
        HamsterConfig.initClients()
        promoIndex = 0
        while True:
            clientIndex = 0
            while clientIndex < HamsterConfig.lenClients:
                HamsterConfig.getHamster(clientIndex).sync()
                HamsterConfig.getHamster(clientIndex).status()
                HamsterConfig.promoGamesCollect(HamsterConfig.getHamster(clientIndex))
                clientIndex += 1
            minDelay = randint(1, 30)
            minDelay += HamsterConfig.minDelay()
            iterTime = time()

            remainsDelay = minDelay
            while time() + 900 < iterTime + minDelay and len(HamsterConfig.promoGamesCollect()) > 0:
                promoClient = HamsterConfig.getHamster(promoIndex)
                if promoClient in HamsterConfig.promoGamesCollect():
                    promoClient.promoGameKeyGen()
                    HamsterConfig.promoGamesCollect(promoClient)    
                promoIndex += 1
                if promoIndex >= HamsterConfig.lenClients:
                    promoIndex = 0
            remainsDelay = int((iterTime + minDelay) - time())
            if remainsDelay > 0:
                
                logger.info(f"Continue in {remainsDelay} sec ({datetime.fromtimestamp(time() + remainsDelay).strftime('%d.%m.%Y, %H:%M:%S')})")
                logger.info("*" * SEP_LENGTH + "\n\n")
                sleep(remainsDelay)
            HamsterConfig.updateConfig()
    except KeyboardInterrupt:
        logger.info("Hamster Kombat Bot terminated")
        return

if __name__ == "__main__":
    main()
