import shlex

import prompt
from valutrade_hub.core.exceptions import InsufficientFundsError, CurrencyNotFoundError, ApiRequestError
from valutrade_hub.core.usecases import (
    buy,
    get_rate,
    login,
    print_help,
    register,
    sell,
    show_portfolio,
)
from valutrade_hub.core.utils import get_codes


def run():
    print("Добро пожаловать в Valutrade!")
    print_help()
    user = None

    while True:
        user_input = prompt.string('Введите команду: ')
        args = shlex.split(user_input)
        cmd_name = args[0] if args else None
        try:
            match cmd_name:
                case "register":
                    register(args[1:])
                case "login": 
                    user = login(args[1:])
                case "show-portfolio": 
                    show_portfolio(args[1:], user)
                case "buy":
                    buy(args[1:], user)
                case "sell": 
                    sell(args[1:], user)
                case "get-rate": 
                    get_rate(args[1:])

                case "help":
                    print_help()

                case "exit":
                    print("Выход из программы.")
                    break
        except InsufficientFundsError as error:
            print(error)
        except CurrencyNotFoundError as error:
            print("Доступны следующие валюты: ")
            get_codes(user)
        except ApiRequestError as error:
            print("Проблемы с сетью, проверьте соединение и повторите позже")