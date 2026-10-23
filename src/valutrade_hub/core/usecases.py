from valutrade_hub.core.models import User, Portfolio
import json
from datetime import datetime, timedelta
from pathlib import Path
from valutrade_hub.core.constants import *

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
            print(f"Неизвестная базовая валюта '{base_currency}'")
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

    portfolio = Portfolio.load(user.user_id)
    rates = portfolio._load_exchange_rates()

    if currency_code not in rates or "USD" not in rates:
        print(f"Не удалось получить курс для {currency_code}→USD")
        return

    rate = rates[currency_code] / rates["USD"]
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

import math


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

    if currency_code not in rates or "USD" not in rates:
        print(f"Не удалось получить курс для {currency_code}→USD")
        return

    rate = rates[currency_code] / rates["USD"]
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
    """Показывает курс одной валюты относительно другой."""
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

    filepath = Path(RATES_STORAGE_PATH)

    try:
        if not filepath.exists():
            rates = DEFAULT_RATES.copy()
            updated_at = datetime.now().isoformat(timespec="seconds")
            is_fresh = False
        else:
            with filepath.open("r", encoding="utf-8") as file:
                data = json.load(file)

            rates = data.get("rates", data)
            updated_at = data.get("updated_at")

            if updated_at:
                update_time = datetime.fromisoformat(updated_at)
                is_fresh = (
                    datetime.now() - update_time < timedelta(minutes=5)
                )
            else:
                is_fresh = False

        if not is_fresh:
            rates = DEFAULT_RATES.copy()
            updated_at = datetime.now().isoformat(timespec="seconds")

            filepath.parent.mkdir(parents=True, exist_ok=True)
            with filepath.open("w", encoding="utf-8") as file:
                json.dump(
                    {
                        "rates": rates,
                        "updated_at": updated_at,
                    },
                    file,
                    ensure_ascii=False,
                    indent=4,
                )

        if from_currency not in rates or to_currency not in rates:
            print(
                f"Курс {from_currency}→{to_currency} недоступен. "
                "Повторите попытку позже."
            )
            return

        rate = rates[to_currency] / rates[from_currency]
        reverse_rate = rates[from_currency] / rates[to_currency]

        print(
            f"Курс {from_currency}→{to_currency}: "
            f"{rate:.2f} "
            f"(обновлено: "
            f"{datetime.fromisoformat(updated_at):%Y-%m-%d %H:%M:%S})"
        )
        print(
            f"Обратный курс {to_currency}→{from_currency}: "
            f"{reverse_rate:.2f}"
        )

    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print(f"Ошибка получения курса: {error}")
        print(
            f"Курс {from_currency}→{to_currency} недоступен. "
            "Повторите попытку позже."
        )