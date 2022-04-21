"""
Define crypto repository components
"""

import base64
import hashlib
import hmac
import json
import time
import urllib.parse
from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Any, Iterable, Optional, Tuple

import attrs
import blockcypher
import requests
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from web3 import Web3
from yaml import dump, load

try:
    from yaml import CDumper as Dumper
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader, Dumper

from cryptomonitor.model import (
    Address,
    Asset,
    Balance,
    Exchanger,
    Exchangerates,
    ExchangerProfile,
    Order,
    Profile,
    Trade,
    Transaction,
    Wallet,
)


class IAssetRepository(metaclass=ABCMeta):
    _address: Address

    @abstractmethod
    def __init__(self, address: str) -> None:
        pass

    @abstractmethod
    def get_balance(self) -> Balance:
        pass


class ETHRepository(IAssetRepository):
    _DEFAULT_NODE = (
        "https://mainnet.infura.io/v3/2d1f7e07e445431dac8287b77fd0a62f"
    )

    def __init__(self, address: str) -> None:
        self._asset = Asset.ETH
        self._address = Address(addr=address, asset=self._asset)
        self._web3_client = Web3(Web3.HTTPProvider(self._DEFAULT_NODE))

    def get_balance(self) -> Balance:
        return Balance(
            asset=self._asset,
            amount=self._web3_client.eth.get_balance(self._address.addr),
        )

    def get_transactions(self) -> int:
        return self._web3_client.eth.get_transaction_count(self._address.addr)

    def scan_transfers_and_swaps(self):
        # TODO: implement this part
        pass


class BTCRepository(IAssetRepository):
    def __init__(self, address: str) -> None:
        self._asset = Asset.BTC
        self._address = Address(addr=address, asset=self._asset)

    def get_balance(self) -> Balance:
        return Balance(
            asset=self._asset,
            amount=blockcypher.get_total_balance(self._address.addr),
        )


class WalletRepository:
    """Sync & return wallets"""

    XRATES_REF = (
        "https://sandbox-api.coinmarketcap.com/v2/tools/price-conversion"
    )

    def __init__(
        self,
        repositories: Iterable[IAssetRepository],
        wallet: Optional[Wallet] = None,
    ):
        self._repositories = set(repositories)
        self._wallet = (
            wallet
            if wallet is not None
            else Wallet(
                balances={
                    balance.asset: balance for balance in self.get_balances()
                },
                exchange_rates=self.get_exchange_rates(),
            )
        )

    def get_balances(self) -> Iterable[Balance]:
        for repository in self._repositories:
            yield repository.get_balance()

    def get_exchange_rates(self) -> Exchangerates:
        # TODO: Convert to & return domain types
        params = {"amount": "1", "symbol": "USDT", "convert": "EUR,BTC,ETH"}
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": "07bf1469-21de-4c07-8910-d35f0f9ecb80",
        }

        session = Session()
        session.headers.update(headers)

        try:
            resp = session.get(self.XRATES_REF, params=params)
            return resp.json()["data"]
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)
            raise


class IExchangeRepository(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, authtoken: str) -> None:
        """Inintiate the Exchange Repository"""

    @abstractmethod
    def get_open_orders(self) -> Tuple[Order]:
        """Returns open orders from the exchanger"""

    @abstractmethod
    def get_balances(self) -> Tuple[Balance, ...]:
        """Returns the balances inside a wallet from the exchanger"""

    @abstractmethod
    def get_trades(self) -> Tuple[Trade]:
        """Returns past trades"""


class KrakenRepository(IExchangeRepository):
    """Implement Kraken exchanger operations"""

    API_URL = "https://api.kraken.com"

    def __init__(self, authtoken: str) -> None:
        """Inintiate the Exchange Repository

        authtoken should take the format: `API_KEY API_SEC`
        """
        self._api_key, self._api_sec = authtoken.split()

    def get_open_orders(self) -> Any:
        """Returns open orders from the exchanger"""
        # TODO: Convert to domain types
        resp = self._kraken_request(
            "/0/private/OpenOrders",
            {"nonce": str(int(1000 * time.time())), "trades": True},
            self._api_key,
            self._api_sec,
        )

        resp_dict = resp.json()

        assert not resp_dict["error"]
        return resp_dict["result"]["open"]

    def get_balances(self) -> Tuple[Balance, ...]:
        """Returns the balances inside a wallet from the exchanger"""
        resp = self._kraken_request(
            "/0/private/Balance",
            {"nonce": str(int(1000 * time.time()))},
            self._api_key,
            self._api_sec,
        )

        resp_dict = resp.json()

        assert not resp_dict["error"]
        return tuple(
            Balance(asset=Asset(asset), amount=float(amount))
            for asset, amount in resp_dict["result"].items()
        )

    def _kraken_request(self, uri_path, data, api_key, api_sec):
        headers = {}
        headers["API-Key"] = api_key
        # get_kraken_signature() as defined in the 'Authentication' section
        headers["API-Sign"] = self._get_kraken_signature(
            uri_path, data, api_sec
        )
        req = requests.post(
            (self.API_URL + uri_path), headers=headers, data=data
        )
        return req

    def _get_kraken_signature(self, urlpath, data, secret):

        postdata = urllib.parse.urlencode(data)
        encoded = (str(data["nonce"]) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest())
        return sigdigest.decode()

    def get_trades(self) -> Tuple[Trade]:
        """Returns past trades"""
        # TODO: Convert to domain types
        resp = self._kraken_request(
            "/0/private/TradesHistory",
            {"nonce": str(int(1000 * time.time())), "trades": True},
            self._api_key,
            self._api_sec,
        )

        resp_dict = resp.json()

        assert not resp_dict["error"]
        return resp_dict["result"]["trades"]


EXCHANGER_TO_REPO = {Exchanger.KRAKEN: KrakenRepository}
ASSET_TO_REPOSITORY = {Asset.BTC: BTCRepository, Asset.ETH: ETHRepository}


def dump_profile(profile: Profile, file_name=".config/profile.yaml") -> None:
    def serializer(_, __, value):
        if isinstance(value, Enum):
            return value.value
        return value

    with open(file_name, "w", encoding="utf-8") as file_out:
        dump(
            attrs.asdict(profile, value_serializer=serializer),
            file_out,
            Dumper=Dumper,
        )


def load_profile(file_name=".config/profile.yaml") -> Profile:
    """Load profile from hard drive"""
    with open(file_name, encoding="utf-8") as file_out:
        profile_dict = load(file_out, Loader=Loader)

    addresses = tuple(
        Address(addr=address_dict["addr"], asset=Asset(address_dict["asset"]))
        for address_dict in profile_dict["addresses"]
    )
    exchangers = tuple(
        ExchangerProfile(
            xchanger=Exchanger(xchanger_dict["xchanger"]),
            authkey=xchanger_dict["authkey"],
        )
        for xchanger_dict in profile_dict["exchangers"]
    )
    return Profile(addresses=addresses, exchangers=exchangers)
