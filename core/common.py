import requests
import sys
import os
import json
from uuid import uuid4
from loguru import logger
from fake_useragent import UserAgent
from time import time, sleep
from random import random, randint, choices
from datetime import datetime
from base64 import b64decode, b64encode
from hashlib import sha256

DOMAIN = "https://api.hamsterkombatgame.io"
PROMO_DOMAIN = "https://api.gamepromo.io/promo"
ACCOUNT_INFO = DOMAIN + "/auth/account-info"
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
        else:
            err_msg = f"Invalid method: {method}"
            return {"error_message": err_msg}
        return response.json()
    except Exception as e:
        err_msg = f"Error: {e}"
        return {"error_message": err_msg}