import hashlib
import json
import secrets
from datetime import datetime
from pathlib import Path

DATA_PATH = "data"
USERS_STORAGE_PATH = f"{DATA_PATH}/users.json"
PORTFOLIOS_STORAGE_PATH = f"{DATA_PATH}/portfolios.json"
RATES_STORAGE_PATH = f"{DATA_PATH}/rates.json"

DEFAULT_RATES = {
        "USD": 1.0,
        "EUR": 1.1,
        "BTC": 60000.0,
    }

class User:
    """Пользователь системы."""

    def __init__(
        self,
        username: str,
        password: str,
        salt: str | None = None,
        registration_date: datetime | None = None,
        user_id: int | None = None,
    ) -> None:
        if not isinstance(username, str) or not username.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self._check_username_unique(username)
        self._user_id = (
            user_id if user_id is not None else self._get_next_user_id()
        )
        self._username = username.strip()
        self._salt = salt if salt is not None else secrets.token_hex(16)
        self._registration_date = (
            registration_date if registration_date is not None else datetime.now()
        )

        self.change_password(password)
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

    def _get_next_user_id(self) -> int:
        """Возвращает следующий свободный ID пользователя."""
        filepath = Path(USERS_STORAGE_PATH)

        if not filepath.exists():
            return 1

        with filepath.open("r", encoding="utf-8") as file:
            content = file.read().strip()
            users = json.loads(content) if content else []

        if not users:
            return 1

        return max(user["user_id"] for user in users) + 1

    def _check_username_unique(self, username: str) -> None:
        """Проверяет, что имя пользователя ещё не занято."""
        filepath = Path(USERS_STORAGE_PATH)

        if not filepath.exists():
            return

        with filepath.open("r", encoding="utf-8") as file:
            content = file.read().strip()
            users = json.loads(content) if content else []

        for user in users:
            if user["username"].casefold() == username.casefold():
                raise ValueError(
                    f"Имя пользователя '{username}' уже занято."
                )

    @classmethod
    def authenticate(cls, username: str, password: str) -> "User":
        """Находит пользователя и проверяет пароль."""
        filepath = Path(USERS_STORAGE_PATH)

        if not filepath.exists():
            raise ValueError("Неверное имя пользователя или пароль.")

        with filepath.open("r", encoding="utf-8") as file:
            content = file.read().strip()
            users = json.loads(content) if content else []

        for user_data in users:
            if user_data["username"].casefold() != username.casefold():
                continue

            salt = user_data["salt"]
            hashed_password = hashlib.sha256(
                (password + salt).encode("utf-8")
            ).hexdigest()

            if not secrets.compare_digest(
                user_data["hashed_password"],
                hashed_password,
            ):
                raise ValueError("Неверный пароль")

            # Восстанавливаем объект без вызова конструктора,
            # который создаёт и сохраняет нового пользователя.
            user = cls.__new__(cls)
            user._user_id = user_data["user_id"]
            user._username = user_data["username"]
            user._salt = salt
            user._hashed_password = user_data["hashed_password"]
            user._registration_date = datetime.fromisoformat(
                user_data["registration_date"]
            )
            return user

        raise ValueError(f"Пользователь '{username}' не найден")

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

class Portfolio:
    """Портфель пользователя со всеми его кошельками."""

    def __init__(
        self,
        user_id: int,
        wallets: dict[str, Wallet] | None = None,
    ) -> None:
        self._user_id = user_id
        self._wallets = wallets if wallets is not None else {}
        self._save_to_json()

    @property
    def user(self) -> User:
        """Возвращает пользователя портфеля."""
        filepath = Path(USERS_STORAGE_PATH)

        with filepath.open("r", encoding="utf-8") as file:
            users = json.load(file)

        for user_data in users:
            if user_data["user_id"] == self._user_id:
                return User(
                    user_id=user_data["user_id"],
                    username=user_data["username"],
                    hashed_password=user_data["hashed_password"],
                    salt=user_data["salt"],
                    registration_date=datetime.fromisoformat(
                        user_data["registration_date"]
                    ),
                )

        raise ValueError(
            f"Пользователь с ID {self._user_id} не найден."
        )

    @property
    def wallets(self) -> dict[str, Wallet]:
        """Возвращает копию словаря кошельков."""
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> None:
        """Добавляет кошелёк для новой валюты."""
        if currency_code in self._wallets:
            raise ValueError(
                f"Кошелёк {currency_code} уже существует."
            )

        self._wallets[currency_code] = Wallet(
            currency_code=currency_code,
            balance=0.0,
        )
        self._save_to_json()

    def get_wallet(self, currency_code: str) -> Wallet:
        """Возвращает кошелёк по коду валюты."""
        try:
            return self._wallets[currency_code]
        except KeyError:
            raise ValueError(
                f"Кошелёк {currency_code} не найден."
            ) from None

    def get_total_value(self, base_currency: str = "USD") -> float:
        """Возвращает стоимость портфеля в базовой валюте."""
        exchange_rates = self._load_exchange_rates()
        if base_currency not in exchange_rates:
            raise ValueError(
                f"Неизвестная валюта: {base_currency}."
            )

        total_usd = 0.0

        for currency_code, wallet in self._wallets.items():
            if currency_code not in exchange_rates:
                raise ValueError(
                    f"Нет курса для валюты {currency_code}."
                )

            total_usd += (
                wallet.balance * exchange_rates[currency_code]
            )

        return total_usd / exchange_rates[base_currency]

    def _save_to_json(self) -> None:
        """Сохраняет портфель в JSON-файл."""
        filepath = Path(PORTFOLIOS_STORAGE_PATH)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if filepath.exists():
            with filepath.open("r", encoding="utf-8") as file:
                content = file.read().strip()
                portfolios = json.loads(content) if content else []
        else:
            portfolios = []

        portfolio_data = {
            "user_id": self._user_id,
            "wallets": {
                currency_code: {
                    "balance": wallet.balance,
                }
                for currency_code, wallet in self._wallets.items()
            },
        }

        for index, portfolio in enumerate(portfolios):
            if portfolio["user_id"] == self._user_id:
                portfolios[index] = portfolio_data
                break
        else:
            portfolios.append(portfolio_data)

        with filepath.open("w", encoding="utf-8") as file:
            json.dump(
                portfolios,
                file,
                ensure_ascii=False,
                indent=4,
            )

    def _load_exchange_rates(self) -> dict[str, float]:
        """Загружает курсы из файла или использует значения по умолчанию."""
        filepath = Path(RATES_STORAGE_PATH)

        if not filepath.exists():
            return DEFAULT_RATES.copy()

        with filepath.open("r", encoding="utf-8") as file:
            content = file.read().strip()

        if not content:
            return DEFAULT_RATES.copy()

        return json.loads(content)
