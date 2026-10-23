#!/usr/bin/env python3
from datetime import datetime

from valutrade_hub.core.models import User


def main() -> None:
    user = User(
    user_id=2,
    username="alice2",
    hashed_password="",
    salt="",
    registration_date=datetime.now(),
)

    # При создании пользователь уже записан в JSON
    user.change_password("qwerty")

    # Изменяем имя — JSON обновляется автоматически
    user.username = "bob"

    print(user.get_user_info())
    print(user.verify_password("qwerty"))


if __name__ == "__main__":
    main()