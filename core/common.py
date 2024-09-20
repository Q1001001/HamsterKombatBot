import requests
import sys
import os
import json
import gc
import urllib
from uuid import uuid4
from loguru import logger
from fake_useragent import UserAgent
from time import time, sleep
from random import random, randint, choices
from datetime import datetime
from base64 import b64decode, b64encode
from hashlib import sha256

DOMAIN = "https://api.hamsterkombatgame.io"
PROMO_DOMAIN = "https://api.gamepromo.io/promo/1"
ACCOUNT_INFO = DOMAIN + "/auth/account-info"
LOGIN = DOMAIN + "/auth/auth-by-telegram-webapp"
BASE_URL = DOMAIN + "/clicker"
UPGRADES_FOR_BUY = BASE_URL + "/upgrades-for-buy"
BUY_UPGRADE = BASE_URL + "/buy-upgrade"
SYNC = BASE_URL + "/sync"
CONFIG = BASE_URL + "/config"
TAP = BASE_URL + "/tap"
BOOSTS_FOR_BUY = BASE_URL + "/boosts-for-buy"
BUY_BOOSTS = BASE_URL + "/buy-boost"
CLAIM_DAILY_CIPHER = BASE_URL + "/claim-daily-cipher"
CLAIM_DAILY_KEYS_MINIGAME = BASE_URL + "/claim-daily-keys-minigame"
START_MINI_GAME = BASE_URL + "/start-keys-minigame"
CHECK_TASKS = BASE_URL + "/check-task"
LIST_TASKS = BASE_URL + "/list-tasks"
CLAIM_DAILY_COMBO = BASE_URL + "/claim-daily-combo"
GET_PROMOS = BASE_URL + "/get-promos"
APPLY_PROMO = BASE_URL + "/apply-promo"

PROMO_LOGIN = PROMO_DOMAIN + "/login-client"
PROMO_REGISTER_EVENT = PROMO_DOMAIN + "/register-event"
PROMO_CREATE_CODE = PROMO_DOMAIN + "/create-code"

SEP_LENGTH = 75

STRING = "abcdefghijklmnopqrstuvwxyz0123456789"

CLIENT_LEVEL = {
    1: "Bronze",
    2: "Silver",
    3: "Gold",
    4: "Platinum",
    5: "Diamond",
    6: "Epic",
    7: "Legendary",
    8: "Master",
    9: "Grandmaster",
    10: "Lord",
    11: "Creator"
}


logger.remove()
logger.add(sys.stdout, colorize=True, level="INFO",
           format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
           "<level>{level: <8}</level> | - <level>{message}</level>")
logger = logger.opt(colors=True)

logger.add("logErrors.txt", level="ERROR",
           format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
           "<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}"
           "</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
           rotation="1 MB")


def request(method: str = "POST", url: str = "", headers: dict = None, data: dict = None) -> dict:
    userAgent = UserAgent().safari
    defaultHeaders = {
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Host": "api.hamsterkombatgame.io",
        "Origin": "https://hamsterkombatgame.io",
        "Referer": "https://hamsterkombatgame.io/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": userAgent,
    }
    if not headers is None:
        for key, value in headers.items():
            defaultHeaders[key] = value
    try:
        if method == "GET":
            response = requests.get(url, headers=defaultHeaders)
        elif method == "POST":
            response = requests.post(
                url, headers=defaultHeaders, data=json.dumps(data))
        elif method == "OPTIONS":
            response = requests.options(url, headers=defaultHeaders)
            response.raise_for_status()
            return {"OPTIONS": response.status_code}
        else:
            err_msg = f"Invalid method: {method}"
            return {"error_message": err_msg}
        response.raise_for_status()
        try:
            jsonData = json.loads(response.text)
        except json.decoder.JSONDecodeError as jsonErr:
            jsonData = {"error_message": f"Error: {jsonErr}"}
        finally:
            return jsonData
    except Exception as e:
        err_msg = f"Error: {e}"
        return {"error_message": err_msg}
    
# Print iterations progress
def ProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)