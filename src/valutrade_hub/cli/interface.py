import shlex

import prompt

from valutrade_hub.core.usecases import print_help, register, login, show_portfolio, buy, sell, get_rate


def run():
    print("Добро пожаловать в Valutrade!")
    print_help()
    user = None

    while True:
        user_input = prompt.string('Введите команду: ')
        args = shlex.split(user_input)
        cmd_name = args[0] if args else None
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