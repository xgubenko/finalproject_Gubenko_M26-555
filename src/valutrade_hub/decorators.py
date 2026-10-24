import logging
from datetime import datetime
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path


def log_action(action: str, verbose: bool = False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger("valutrade.actions")
            logger.setLevel(logging.INFO)

            # Настраиваем файловый обработчик один раз
            if not any(
                isinstance(handler, RotatingFileHandler)
                and handler.baseFilename
                == str(Path("logs/actions.log").resolve())
                for handler in logger.handlers
            ):
                log_path = Path("logs/actions.log").resolve()
                log_path.parent.mkdir(parents=True, exist_ok=True)

                handler = RotatingFileHandler(
                    log_path,
                    maxBytes=5 * 1024 * 1024,
                    backupCount=3,
                    encoding="utf-8",
                )
                handler.setFormatter(logging.Formatter("%(message)s"))
                logger.addHandler(handler)

            timestamp = datetime.now().astimezone().isoformat(
                timespec="seconds"
            )
            user = args[1] if len(args) > 1 else kwargs.get("user")
            username = getattr(user, "username", None) or "anonymous"

            fields = [
                timestamp,
                f"action={action}",
                f"user={username}",
            ]

            if verbose:
                fields.append(f"args={args[0]!r}")

            try:
                result = func(*args, **kwargs)
            except Exception as error:
                fields.extend([
                    "result=ERROR",
                    f"error={type(error).__name__}: {error}",
                ])
                logger.info(" ".join(fields))
                raise

            fields.append("result=OK")
            logger.info(" ".join(fields))
            return result

        return wrapper

    return decorator