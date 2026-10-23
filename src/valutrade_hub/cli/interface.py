import shlex

import prompt

from valutrade_hub.core.usecases import print_help, register, login


def run():
    print("Добро пожаловать в Valutrade!")
    print_help()

    while True:
        user_input = prompt.string('Введите команду: ')
        args = shlex.split(user_input)
        cmd_name = args[0] if args else None
        user = None

        match cmd_name:

            case "register":
                register(args[1:])
            case "login": 
                user = login(args[1:])
            case "show-portfolio": pass
            case "buy": 
                if user == None:
                    print("Требуется вход в учетную запись")
                    continue
            case "sell": pass
            case "get-rate": pass

            case "help":
                print_help()

            case "exit":
                print("Выход из программы.")
                break