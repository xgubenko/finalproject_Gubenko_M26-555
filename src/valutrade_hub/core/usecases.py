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