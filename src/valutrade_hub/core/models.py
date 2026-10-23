import hashlib
import json
import secrets
from datetime import datetime
from pathlib import Path

DATA_PATH = "data"
USERS_STORAGE_PATH = f"{DATA_PATH}/users.json"
PORTFOLIOS_STORAGE_PATH = f"{DATA_PATH}/portfolios.json"
RATES_STORAGE_PATH = f"{DATA_PATH}/rates.json"

class Wallet:
    """Кошелёк пользователя для одной конкретной валюты."""
    def __init__(self, currency_code: str, balance: float = 0) -> None:
        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым.")
        if balance < 0:
            raise ValueError("Баланс не может быть отрицательным.")
        self._currency_code = currency_code
        self._balance = balance

    @property
    def balance(self) -> float:
        """Возвращает баланс кошелька."""
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise ValueError("Баланс должен быть числом.")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        """Пополнение баланса."""
        self._validate_amount(amount)
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        """Снятие с баланса."""
        self._validate_amount(amount)
        if amount > self._balance:
            raise ValueError("Нельзя снять больше чем есть на балансе.")
        self._balance -= amount

    def get_balance_info(self) -> dict:
        """Получение информации о балансе."""
        return {
            "currency_code": self._currency_code,
            "balance": self._balance,
        }

    @staticmethod
    def _validate_amount(amount: float) -> None:
        """Проверяет сумму операции."""
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise ValueError("Сумма должна быть числом.")
        

class User:
    """Пользователь системы."""

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ) -> None:
        if not isinstance(username, str) or not username.strip():
            raise ValueError("Имя пользователя не может быть пустым.")

        self._user_id = user_id
        self._username = username.strip()
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

        self._save_to_json()

    @property
    def user_id(self) -> int:
        """Возвращает идентификатор пользователя."""
        return self._user_id

    @property
    def username(self) -> str:
        """Возвращает имя пользователя."""
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        """Изменяет имя пользователя и сохраняет изменения."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")

        self._username = value.strip()
        self._save_to_json()

    @property
    def hashed_password(self) -> str:
        """Возвращает хеш пароля."""
        return self._hashed_password

    @property
    def salt(self) -> str:
        """Возвращает соль пользователя."""
        return self._salt

    @property
    def registration_date(self) -> datetime:
        """Возвращает дату регистрации."""
        return self._registration_date

    def get_user_info(self) -> dict:
        """Возвращает информацию о пользователе без пароля и соли."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> None:
        """Изменяет пароль и сохраняет изменения в JSON."""
        if not isinstance(new_password, str) or len(new_password) < 4:
            raise ValueError(
                "Пароль должен содержать не менее 4 символов."
            )

        salt = secrets.token_hex(16)
        hashed_password = hashlib.sha256(
            (new_password + salt).encode("utf-8")
        ).hexdigest()

        self._salt = salt
        self._hashed_password = hashed_password

        self._save_to_json()

    def verify_password(self, password: str) -> bool:
        """Проверяет введённый пароль."""
        if not isinstance(password, str):
            return False

        hashed_password = hashlib.sha256(
            (password + self._salt).encode("utf-8")
        ).hexdigest()

        return secrets.compare_digest(
            self._hashed_password,
            hashed_password,
        )

    def _save_to_json(self) -> None:
        """Сохраняет пользователя в JSON-файл."""
        filepath = Path(USERS_STORAGE_PATH)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if filepath.exists():
            with filepath.open("r", encoding="utf-8") as file:
                users = json.load(file)
        else:
            users = []

        user_data = {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }

        for index, user in enumerate(users):
            if user["user_id"] == self._user_id:
                users[index] = user_data
                break
        else:
            users.append(user_data)

        with filepath.open("w", encoding="utf-8") as file:
            json.dump(users, file, ensure_ascii=False, indent=4)

