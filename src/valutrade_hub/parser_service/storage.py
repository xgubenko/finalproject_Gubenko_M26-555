
import json
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from valutrade_hub.parser_service.config import ParserConfig

logger = logging.getLogger(__name__)


class RatesStorage:
    """Хранилище текущих курсов и истории их обновлений."""

    def __init__(self, config: ParserConfig | None = None) -> None:
        self.config = config or ParserConfig()
        self.rates_path = Path(self.config.RATES_FILE_PATH)
        self.history_path = Path(self.config.HISTORY_FILE_PATH)

    def _read_json(self, path: Path, default: Any) -> Any:
        """Читает JSON-файл. Если файл отсутствует, возвращает default."""
        if not path.exists():
            return default

        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Некорректный JSON в файле {path}"
            ) from error

    @staticmethod
    def _write_json_atomic(path: Path, data: Any) -> None:
        """Атомарно записывает JSON через временный файл."""
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None

        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                suffix=".tmp",
                delete=False,
            ) as file:
                temp_path = Path(file.name)
                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=4,
                )
                file.write("\n")

            temp_path.replace(path)

        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()

    def load_rates(self) -> dict:
        """Загружает текущий кэш курсов."""
        data = self._read_json(self.rates_path, {})

        if not isinstance(data, dict):
            raise ValueError("Некорректный формат rates.json")

        return data

    def save_rates(self, snapshot: dict) -> None:
        """Обновляет кэш, сохраняя более свежие значения пар."""
        if not isinstance(snapshot.get("pairs"), dict):
            raise ValueError("В снимке отсутствует словарь pairs")

        current = self.load_rates()
        current_pairs = current.get("pairs", {})

        if not isinstance(current_pairs, dict):
            raise ValueError("Некорректный формат pairs в rates.json")

        updated_pairs = dict(current_pairs)

        for pair, new_value in snapshot["pairs"].items():
            if not isinstance(new_value, dict):
                logger.warning("Пропускаем некорректную пару %s", pair)
                continue

            rate = new_value.get("rate")
            updated_at = new_value.get("updated_at")

            if (
                not isinstance(rate, (int, float))
                or isinstance(rate, bool)
                or rate <= 0
                or not isinstance(updated_at, str)
            ):
                logger.warning("Пропускаем некорректный курс %s", pair)
                continue

            old_value = updated_pairs.get(pair)

            if isinstance(old_value, dict):
                old_timestamp = old_value.get("updated_at", "")

                if isinstance(old_timestamp, str) and old_timestamp > updated_at:
                    continue

            updated_pairs[pair] = new_value

        last_refresh = snapshot.get("last_refresh", "")

        if not isinstance(last_refresh, str):
            raise ValueError("Некорректный last_refresh")

        old_refresh = current.get("last_refresh", "")
        if isinstance(old_refresh, str):
            last_refresh = max(last_refresh, old_refresh)

        result = {
            "pairs": updated_pairs,
            "last_refresh": last_refresh,
        }

        self._write_json_atomic(self.rates_path, result)
        logger.info("Rates cache saved: %d pairs", len(updated_pairs))

    def load_history(self) -> list[dict]:
        """Загружает историю курсов."""
        data = self._read_json(self.history_path, [])

        if not isinstance(data, list):
            raise ValueError(
                "История курсов должна храниться в виде JSON-массива"
            )

        return data

    def append_history(self, records: list[dict]) -> None:
        """Добавляет записи в историю, исключая дубликаты по id."""
        if not records:
            logger.info("No history records to append")
            return

        history = self.load_history()
        existing_ids = {
            record["id"]
            for record in history
            if isinstance(record, dict) and isinstance(record.get("id"), str)
        }

        for record in records:
            if not isinstance(record, dict):
                logger.warning("Пропускаем некорректную запись истории")
                continue

            record_id = record.get("id")

            if not isinstance(record_id, str) or not record_id:
                logger.warning("Пропускаем запись без корректного id")
                continue

            if record_id in existing_ids:
                continue

            history.append(record)
            existing_ids.add(record_id)

        self._write_json_atomic(self.history_path, history)
        logger.info("History saved: %d records", len(history))
