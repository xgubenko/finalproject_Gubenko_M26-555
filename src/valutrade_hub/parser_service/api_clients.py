
from abc import ABC, abstractmethod

import requests

from valutrade_hub.core.exceptions import ApiRequestError
from valutrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    """Базовый класс для клиентов API курсов валют."""

    def __init__(self, config: ParserConfig | None = None) -> None:
        self.config = config or ParserConfig()

    @abstractmethod
    def fetch_rates(self) -> dict[str, float]:
        """Получает курсы и возвращает словарь пар валют."""
        pass

    def _get_json(self, url: str, params: dict | None = None) -> dict:
        """Выполняет GET-запрос и возвращает JSON-ответ."""
        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as error:
            raise ApiRequestError(
                f"Ошибка запроса к API: {error}"
            ) from error
        except ValueError as error:
            raise ApiRequestError(
                "API вернул некорректный JSON"
            ) from error

        if not isinstance(data, dict):
            raise ApiRequestError("Некорректный формат ответа API")

        return data


class CoinGeckoClient(BaseApiClient):
    """Клиент для получения курсов криптовалют через CoinGecko."""

    def fetch_rates(self) -> dict[str, float]:
        currency_ids = self.config.CRYPTO_ID_MAP
        params = {
            "ids": ",".join(currency_ids.values()),
            "vs_currencies": self.config.BASE_CURRENCY.lower(),
        }

        data = self._get_json(
            "https://api.coingecko.com/api/v3/simple/price",
            params=params,
        )

        rates = {}
        base_currency = self.config.BASE_CURRENCY

        for code, currency_id in currency_ids.items():
            currency_data = data.get(currency_id)

            if not isinstance(currency_data, dict):
                continue

            rate = currency_data.get(base_currency.lower())

            if (
                isinstance(rate, (int, float))
                and not isinstance(rate, bool)
                and rate > 0
            ):
                rates[f"{code}_{base_currency}"] = float(rate)

        if not rates:
            raise ApiRequestError(
                "CoinGecko не вернул корректных курсов криптовалют"
            )

        return rates


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для получения курсов фиатных валют."""

    def fetch_rates(self) -> dict[str, float]:
        data = self._get_json(self.config.GET_FIAT_REQUEST)

        if data.get("result") != "success":
            raise ApiRequestError(
                f"ExchangeRate-API вернул ошибку: "
                f"{data.get('error-type', 'неизвестная ошибка')}"
            )

        conversion_rates = data.get("conversion_rates")

        if not isinstance(conversion_rates, dict):
            raise ApiRequestError(
                "ExchangeRate-API не вернул словарь conversion_rates"
            )

        base_currency = self.config.BASE_CURRENCY
        rates = {}

        for code in self.config.FIAT_CURRENCIES:
            rate = conversion_rates.get(code)

            if (
                isinstance(rate, (int, float))
                and not isinstance(rate, bool)
                and rate > 0
            ):
                # API с базой USD возвращает количество валюты за 1 USD.
                # Инвертируем курс, чтобы получить CODE_USD.
                rates[f"{code}_{base_currency}"] = 1.0 / rate

        if not rates:
            raise ApiRequestError(
                "ExchangeRate-API не вернул корректных курсов валют"
            )

        return rates
