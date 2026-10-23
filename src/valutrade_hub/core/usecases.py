from valutrade_hub.core.models import User, Portfolio
import shlex

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