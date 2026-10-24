from valutrade_hub.core.models import Portfolio, User


def get_codes(user: User) -> list[str]:
    portfolio = Portfolio.load(user.user_id)
    print(portfolio._load_exchange_rates())