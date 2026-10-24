
import logging
from datetime import datetime, timezone

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import BaseApiClient
from valutatrade_hub.parser_service.storage import RatesStorage


logger = logging.getLogger(__name__)


class RatesUpdater:
    """Обновляет курсы валют и сохраняет их в хранилища."""

    def __init__(
        self,
        clients: list[BaseApiClient],
        storage: RatesStorage,
    ) -> None:
        self.clients = clients
        self.storage = storage

    def run_update(self) -> int:
        """Обновляет курсы. Возвращает количество обновлённых пар."""
        logger.info("Starting rates update")

        timestamp = datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z")

        all_rates: dict[str, float] = {}
        history: list[dict] = []
        errors: list[str] = []

        for client in self.clients:
            source = type(client).__name__.removesuffix("Client")

            logger.info("Fetching rates from %s", source)

            try:
                rates = client.fetch_rates()
            except ApiRequestError as error:
                logger.exception("Failed to fetch rates from %s", source)
                errors.append(f"{source}: {error}")
                continue
            except Exception as error:
                logger.exception("Unexpected error from %s", source)
                errors.append(f"{source}: {error}")
                continue

            logger.info("Received %d rates from %s", len(rates), source)

            for pair, rate in rates.items():
                if not isinstance(rate, (int, float)) or isinstance(rate, bool):
                    logger.warning("Skipping invalid rate for %s", pair)
                    continue

                if rate <= 0:
                    logger.warning("Skipping non-positive rate for %s", pair)
                    continue

                all_rates[pair] = float(rate)

                from_currency, to_currency = pair.split("_", maxsplit=1)

                history.append({
                    "id": f"{pair}_{timestamp}",
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "rate": float(rate),
                    "timestamp": timestamp,
                    "source": source,
                    "meta": {},
                })

        if not all_rates:
            logger.error("No rates were received; storage was not updated")
            if errors:
                raise ApiRequestError(
                    "Не удалось получить курсы ни от одного источника: "
                    + "; ".join(errors)
                )
            return 0

        snapshot = {
            "pairs": {
                pair: {
                    "rate": rate,
                    "updated_at": timestamp,
                    "source": self._get_source(pair),
                }
                for pair, rate in all_rates.items()
            },
            "last_refresh": timestamp,
        }

        logger.info("Saving %d rates", len(all_rates))

        self.storage.save_rates(snapshot)
        self.storage.append_history(history)

        if errors:
            logger.warning(
                "Rates update completed with errors: %s",
                "; ".join(errors),
            )
        else:
            logger.info("Rates update completed successfully")

        return len(all_rates)

    def _get_source(self, pair: str) -> str:
        """Определяет источник курса по клиенту, вернувшему пару."""
        for client in self.clients:
            try:
                if pair in client.fetch_rates():
                    return type(client).__name__.removesuffix("Client")
            except Exception:
                continue

        return "unknown"
