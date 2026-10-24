import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import math
from valutrade_hub.core.exceptions import CurrencyNotFoundError
from valutrade_hub.core.models import Portfolio, User
from valutrade_hub.decorators import log_action
from valutrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutrade_hub.parser_service.config import ParserConfig
from valutrade_hub.parser_service.storage import RatesStorage
from valutrade_hub.parser_service.updater import RatesUpdater


def print_help():
    """Prints the help message for the current mode."""
   
    print("\n***Процесс работы с Valutrade***")
    print("Функции:")
    print("<command> register - зарегестрироваться")
    print("<command> login - войти в систему")
    print("<command> show-portfolio - посмотреть свой портфель и балансы")
    print("<command> buy - купить валюту")
    print("<command> sell - продать валюту")
    print("<command> get-rate - получить курс валюты")
    
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")

def register(args: list[str]) -> None:
    """Регистрирует нового пользователя."""
    options = dict(zip(args[::2], args[1::2]))

    if set(options) != {"--username", "--password"} or len(args) != 4:
        print(
            "Использование: "
            "register --username <имя> --password <пароль>"
        )
        return
    try:
        user = User(
            username=options["--username"],
            password=options["--password"],
        )
        Portfolio(user.user_id)
    except ValueError as error:
        print(f"Ошибка регистрации: {error}")
        return

    print(f"Пользователь '{user.username}' зарегистрирован (id={user.user_id}).\
 Войдите: login --username {user.username} --password ****")

def login(args: list[str]) -> User:
    """Возвращает учетную запись пользователя после авторизации."""
    options = dict(zip(args[::2], args[1::2]))

    if set(options) != {"--username", "--password"} or len(args) != 4:
        raise ValueError(
            "Использование: login --username <имя> --password <пароль>"
        )
    try:
        user = User.authenticate(
            username=options["--username"],
            password=options["--password"],
        )
    except ValueError as error:
        print(f"{error}")
        return None

    print(f"Вы вошли как '{user.username}'")
    return user

def show_portfolio(
    args: list[str],
    user: User | None,
) -> None:
    """Показывает кошельки и итоговую стоимость портфеля."""
    if user is None:
        print("Сначала выполните login")
        return


    base_currency = "USD"

    if len(args) == 2:
        base_currency = args[1].upper()

    portfolio = Portfolio.load(user.user_id)

    try:
        # Проверяем валюту даже при отсутствии кошельков.
        portfolio.get_total_value(base_currency)
    except ValueError as error:
        if base_currency not in portfolio._load_exchange_rates():
            raise CurrencyNotFoundError(base_currency)
        else:
            print(error)
        return

    wallets = portfolio.wallets

    total = 0.0

    for currency_code, wallet in wallets.items():
        try:
            value = portfolio.get_wallet_value(
                currency_code,
                base_currency,
            )
        except ValueError as error:
            print(f"Ошибка расчёта: {error}")
            return

        total += value

    print(f"Портфель пользователя '{user.username}' (база: {base_currency}):")

    for currency_code, wallet in wallets.items():
        precision = 4 if currency_code == "BTC" else 2
        value = portfolio.get_wallet_value(currency_code, base_currency)

        print(
            f"- {currency_code}: "
            f"{wallet.balance:.{precision}f}  → "
            f"{value:,.2f} {base_currency}"
        )

    print("-" * 33)
    print(f"ИТОГО: {total:,.2f} {base_currency}")

@log_action("BUY", True)
def buy(args: list[str], user: User | None) -> None:
    """Покупает валюту и добавляет её в портфель."""
    if user is None:
        print("Сначала выполните login")
        return

    if (
        len(args) != 4
        or args[0] != "--currency"
        or args[2] != "--amount"
    ):
        print("Использование: buy --currency <валюта> --amount <сумма>")
        return

    currency_code = args[1].upper()

    if (
        len(currency_code) != 3
        or not currency_code.isalpha()
        or not currency_code.isascii()
    ):
        print("Некорректный формат валюты")
        return

    try:
        amount = float(args[3])
    except ValueError:
        print("'amount' должен быть положительным числом")
        return

    if not math.isfinite(amount) or amount <= 0:
        print("'amount' должен быть положительным числом")
        return

    portfolio = Portfolio.load(user.user_id)
    rates = portfolio._load_exchange_rates()

    if not isinstance(rates, dict):
        print("Не удалось загрузить курсы валют")
        return

    # Поддержка формата {"rates": {...}}
    if "rates" in rates and isinstance(rates["rates"], dict):
        rates = rates["rates"]

    # Для USD курс к USD всегда равен 1
    if currency_code == "USD":
        rate = 1.0
    else:
        if currency_code not in rates or "USD" not in rates:
            print(f"Не удалось получить курс для {currency_code}→USD")
            return

        try:
            rate = float(rates[currency_code]) / float(rates["USD"])
        except (TypeError, ValueError, ZeroDivisionError):
            print(f"Некорректные данные курса для {currency_code}→USD")
            return

        if not math.isfinite(rate) or rate <= 0:
            print(f"Некорректные данные курса для {currency_code}→USD")
            return

    purchase_value = amount * rate

    if currency_code not in portfolio.wallets:
        portfolio.add_currency(currency_code)

    wallet = portfolio.get_wallet(currency_code)
    old_balance = wallet.balance

    wallet.deposit(amount)
    new_balance = wallet.balance

    portfolio._save_to_json()

    precision = 4 if currency_code == "BTC" else 2

    print(
        f"Покупка выполнена: {amount:.{precision}f} "
        f"{currency_code} по курсу {rate:,.2f} USD/{currency_code}"
    )
    print("Изменения в портфеле:")
    print(
        f"- {currency_code}: "
        f"было {old_balance:.{precision}f} → "
        f"стало {new_balance:.{precision}f}"
    )
    print(f"Оценочная стоимость покупки: {purchase_value:,.2f} USD")

@log_action("SELL", True)
def sell(args: list[str], user: User | None) -> None:
    """Продаёт валюту из портфеля пользователя."""
    if user is None:
        print("Сначала выполните login")
        return

    if args and args[0] == "sell":
        args = args[1:]

    if (
        len(args) != 4
        or args[0] != "--currency"
        or args[2] != "--amount"
    ):
        print("Использование: sell --currency <валюта> --amount <сумма>")
        return

    currency_code = args[1].upper()

    if (
        len(currency_code) != 3
        or not currency_code.isalpha()
        or not currency_code.isascii()
    ):
        print("Некорректный формат валюты")
        return

    try:
        amount = float(args[3])
    except ValueError:
        print("'amount' должен быть положительным числом")
        return

    if not math.isfinite(amount) or amount <= 0:
        print("'amount' должен быть положительным числом")
        return

    portfolio = Portfolio.load(user.user_id)

    try:
        wallet = portfolio.get_wallet(currency_code)
    except ValueError:
        print(
            f"У вас нет кошелька '{currency_code}'. "
            "Добавьте валюту: она создаётся автоматически при первой покупке."
        )
        return

    precision = 4 if currency_code == "BTC" else 2

    if wallet.balance < amount:
        print(
            f"Недостаточно средств: доступно "
            f"{wallet.balance:.{precision}f} {currency_code}, "
            f"требуется {amount:.{precision}f} {currency_code}"
        )
        return

    rates = portfolio._load_exchange_rates()

    if not isinstance(rates, dict):
        print("Не удалось загрузить курсы валют")
        return

    # Поддержка формата {"rates": {...}}
    if "rates" in rates and isinstance(rates["rates"], dict):
        rates = rates["rates"]

    # USD → USD: курс всегда равен 1
    if currency_code == "USD":
        rate = 1.0
    else:
        if currency_code not in rates or "USD" not in rates:
            print(f"Не удалось получить курс для {currency_code}→USD")
            return

        try:
            rate = float(rates[currency_code]) / float(rates["USD"])
        except (TypeError, ValueError, ZeroDivisionError):
            print(f"Некорректные данные курса для {currency_code}→USD")
            return

        if not math.isfinite(rate) or rate <= 0:
            print(f"Некорректные данные курса для {currency_code}→USD")
            return

    revenue = amount * rate
    old_balance = wallet.balance

    wallet.withdraw(amount)
    new_balance = wallet.balance

    portfolio._save_to_json()

    print(
        f"Продажа выполнена: {amount:.{precision}f} "
        f"{currency_code} по курсу {rate:,.2f} USD/{currency_code}"
    )
    print("Изменения в портфеле:")
    print(
        f"- {currency_code}: было "
        f"{old_balance:.{precision}f} → "
        f"стало {new_balance:.{precision}f}"
    )
    print(f"Оценочная выручка: {revenue:,.2f} USD")


def get_rate(args: list[str]) -> None:
    """Показывает курс валют и обновляет устаревший кэш."""

    if (
        len(args) != 4
        or args[0] != "--from"
        or args[2] != "--to"
    ):
        print("Использование: get-rate --from <валюта> --to <валюта>")
        return

    from_currency = args[1].upper()
    to_currency = args[3].upper()

    for currency in (from_currency, to_currency):
        if (
            len(currency) != 3
            or not currency.isalpha()
            or not currency.isascii()
        ):
            print(f"Некорректный код валюты: {currency}")
            return

    config = ParserConfig()
    storage = RatesStorage(config)
    filepath = Path(config.RATES_FILE_PATH)

    def parse_timestamp(value: str) -> datetime:
        """Преобразует ISO-время в UTC."""
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        return timestamp.astimezone(timezone.utc)

    def load_cache() -> tuple[dict, bool]:
        """Возвращает курсы и признак актуальности нужных валют."""
        if not filepath.exists():
            return {}, False

        with filepath.open("r", encoding="utf-8") as file:
            data = json.load(file)

        now = datetime.now(timezone.utc)

        # Новый формат Parser Service: pairs -> EUR_USD -> rate, updated_at
        if isinstance(data.get("pairs"), dict):
            pairs = data["pairs"]
            rates = {"USD": 1.0}
            fresh = True

            for currency in (from_currency, to_currency):
                if currency == "USD":
                    continue

                pair = pairs.get(f"{currency}_USD")

                if not isinstance(pair, dict):
                    fresh = False
                    continue

                rate = pair.get("rate")
                updated_at = pair.get("updated_at")

                if (
                    not isinstance(rate, (int, float))
                    or isinstance(rate, bool)
                    or rate <= 0
                    or not isinstance(updated_at, str)
                ):
                    fresh = False
                    continue

                rates[currency] = float(rate)

                try:
                    if now - parse_timestamp(updated_at) >= timedelta(minutes=5):
                        fresh = False
                except ValueError:
                    fresh = False

            return rates, fresh

        # Старый формат: rates + единое updated_at
        rates = data.get("rates", data)
        updated_at = data.get("updated_at")

        if not isinstance(rates, dict) or not isinstance(updated_at, str):
            return {}, False

        try:
            fresh = (
                now - parse_timestamp(updated_at) < timedelta(minutes=5)
            )
        except ValueError:
            fresh = False

        return rates, fresh

    try:
        rates, is_fresh = load_cache()

        if not is_fresh:
            print("Кэш курсов устарел. Обновляем...")

            updater = RatesUpdater(
                clients=[
                    CoinGeckoClient(config),
                    ExchangeRateApiClient(config),
                ],
                storage=storage,
            )

            try:
                updater.run_update()
            except Exception as error:
                print(f"Не удалось обновить курсы: {error}")

            # Перечитываем кэш, даже если обновление завершилось ошибкой.
            rates, _ = load_cache()

        if from_currency not in rates or to_currency not in rates:
            print(
                f"Курс {from_currency}→{to_currency} недоступен. "
                "Повторите попытку позже."
            )
            return

        # В новом формате значения — стоимость валюты в USD.
        # В старом формате rates содержит количество валюты за 1 USD.
        with filepath.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data.get("pairs"), dict):
            rate = rates[from_currency] / rates[to_currency]
            reverse_rate = 1 / rate
            timestamps = [
                data["pairs"][f"{currency}_USD"]["updated_at"]
                for currency in (from_currency, to_currency)
                if currency != "USD"
                and isinstance(
                    data["pairs"].get(f"{currency}_USD"), dict
                )
            ]
            updated_at = min(timestamps) if timestamps else data.get(
                "last_refresh", "неизвестно"
            )
        else:
            rate = rates[to_currency] / rates[from_currency]
            reverse_rate = 1 / rate
            updated_at = data.get("updated_at", "неизвестно")

        print(
            f"Курс {from_currency}→{to_currency}: {rate:.6f} "
            f"(обновлено: {updated_at})"
        )
        print(
            f"Обратный курс {to_currency}→{from_currency}: "
            f"{reverse_rate:.6f}"
        )

    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print(f"Ошибка получения курса: {error}")