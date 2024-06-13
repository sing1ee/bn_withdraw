from binance.client import Client


class Binance:
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, api_secret)

    def withdraw(self, coin, address, amount, network):
        return self.client.withdraw(
            coin=coin,
            address=address,
            amount=amount,
            network=network,
        )

    def all_coins(self):
        return self.client.get_all_coins_info()
