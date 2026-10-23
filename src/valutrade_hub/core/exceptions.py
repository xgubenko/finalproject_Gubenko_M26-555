class InsufficientFundsError(ValueError):
    """Недостаточно средств для выполнения операции."""

    def __init__(
        self,
        available: float,
        required: float,
        code: str,
    ) -> None:
        self.available = available
        self.required = required
        self.code = code

        super().__init__(
            f"Недостаточно средств: доступно "
            f"{available:g} {code}, требуется {required:g} {code}"
        )


class CurrencyNotFoundError(LookupError):
    """Неизвестная валюта."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")


class ApiRequestError(RuntimeError):
    """Ошибка при обращении к внешнему API."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            f"Ошибка при обращении к внешнему API: {reason}"
        )