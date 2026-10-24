


CRYPTO_ID_MAP = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"} 

import os
from dataclasses import dataclass

@dataclass
class ParserConfig:
    # Ключ загружается из переменной окружения
    DEV_API_KEY = "f1176e21dd406a384d09d6aa"
    key = os.getenv("EXCHANGERATE_API_KEY")
    if key == None:
        key = DEV_API_KEY
    EXCHANGERATE_API_KEY: str = key

    # Эндпоинты
    GET_FIAT_REQUEST = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/USD"
    GET_CRYPTO_REQUEST = f"https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd"

    # Списки валют
    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "SOL")
    CRYPTO_ID_MAP: dict = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
    }

    # Пути
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10