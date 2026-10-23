from valutrade_hub.core.models import User
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

def register(args: list[str]):
    if(len(args) < 5):
        print("Введенная команда некорректна")
        return
#     > register --username alice --password 1234
# Пользователь 'alice' зарегистрирован (id=3). Войдите: login --username alice --password ****
    user = User(username = args[2], password=args[4])
    print(f"Пользователь '{user.username}' зарегистрирован (id={user.user_id}). Войдите: login --username {user.username} --password ****")