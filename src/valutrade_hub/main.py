#!/usr/bin/env python3
from datetime import datetime

from valutrade_hub.core.models import User, Portfolio


def main() -> None:
    user = User(
    user_id=1,
    username="alice2",
    hashed_password="",
    salt="",
    registration_date=datetime.now(),
)

    # При создании пользователь уже записан в JSON
    user.change_password("qwerty")

    # Изменяем имя — JSON обновляется автоматически
    user.username = "bob"


    portfolio = Portfolio(user_id=2)
    portfolio.add_currency("USD")
    portfolio.add_currency("BTC")


if __name__ == "__main__":
    main()