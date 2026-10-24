# Платформа для отслеживания и симуляции торговли валютами
## Общая идея проекта
```text
Основной Сервис (Core Service): Главное приложение, которое предоставляет пользовательский интерфейс (CLI), управляет пользователями, их кошельками, историей транзакций и взаимодействует с сервисом парсинга для получения актуальных курсов.
```
```text
Сервис Парсинга (Parser Service): Отдельное приложение, которое по запросу или расписанию обращается к публичным API, получает актуальные курсы, сравнивает их с предыдущими значениями и сохраняет историю в базу данных.
```
## Сборка и запуск проекта
```bash
uv build
uvx twine check dist/*
uv tool install dist/*.whl
valutrade
```
## Ruff
### Проверка всего проекта
```bash
uv run ruff check .
```
### Проверка отдельного файла
```bash
uv run ruff check path/to/file.py
```
Замените `path/to/file.py` на путь к проверяемому Python-файлу.

## Использование команд
### Регистрация пользователя
```text
register --username testuser --password asdf
```
### Логин
```text
login --username testuser --password asdf
```
### Показать портфолио
```text
show-portfolio —base EUR
```
### Покупка валюты
```text
buy --currency USD --amount 1
```
### Продажа валюты
```text
sell --currency USD --amount 0.5 
```
### Показать валютную пару
```text
get-rate --from USD --to EUR
```
### Помощь
```text
help
```
### Выход
```text
exit
```
## play asciinema demo
```bash
asciinema play demo.cast
```
```text
```text
https://asciinema.org/a/ioP4AHMzDiELd3Et
```