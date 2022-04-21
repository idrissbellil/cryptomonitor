"""Define domain models"""

from enum import Enum
from typing import FrozenSet, Mapping, Set, Tuple, Union

from attrs import define


class Asset(Enum):
    BTC = "BTC"
    ETH = "ETH"
    USD = "USD"
    EUR = "EUR"


CRYPTO_ASSETS = {Asset.BTC, Asset.ETH}
FIAT_ASSETS = {Asset.USD, Asset.EUR}


class OrderStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@define(kw_only=True)
class Address:
    addr: str
    asset: Asset


class Exchanger(Enum):
    KRAKEN = "KRAKEN"


@define(kw_only=True)
class ExchangerProfile:
    xchanger: Exchanger
    authkey: str


@define(kw_only=True)
class Profile:
    addresses: Tuple[Address, ...]
    exchangers: Tuple[ExchangerProfile, ...]


@define(kw_only=True)
class Balance:
    """Blance object storing information enough to distinguish a balance"""

    asset: Asset
    amount: float


@define(kw_only=True)
class Transaction:
    asset_orig: Address
    asset_dest: Address
    amount_orig: float


@define(kw_only=True)
class Trade:
    asset_orig: Address
    asset_dest: Address
    amount_orig: float
    amount_dest: float


@define(kw_only=True)
class Order:
    asset_orig: Address
    asset_dest: Address
    amount_orig: float
    amount_dest: float
    status: OrderStatus


@define(kw_only=True)
class Exchangerates:
    @define(kw_only=True)
    class Rate:
        asset: Asset
        value: float

    base_asset: Asset
    rates: Set[Rate]

    _xrate_matrix: Mapping[Asset, Mapping[Asset, Balance]]


@define(kw_only=True)
class Wallet:
    """Interface for common wallet usage"""

    balances: Mapping[Asset, Balance]
    exchange_rates: Exchangerates

    def convert(self, asset: Asset) -> Tuple[Balance]:
        """Convert all the balances to one asset"""
