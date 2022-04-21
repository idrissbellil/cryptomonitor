import argparse
import logging

from cryptomonitor.model import (
    Address,
    Asset,
    CRYPTO_ASSETS,
    ExchangerProfile,
    Profile,
)
from cryptomonitor.repository import (
    ASSET_TO_REPOSITORY,
    dump_profile,
    Exchanger,
    EXCHANGER_TO_REPO,
    load_profile,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s:%(lineno)s  %(message)s",
)

log = logging.getLogger("cryptomonitor")


def init(args: argparse.Namespace) -> None:
    """Persists profile for future use"""
    assets = args.asset
    addresses = args.address
    exchangers = args.exchanger_name
    exchanger_keys = args.exchanger_key

    if len(assets) != len(addresses):
        raise ValueError("The number of assets & addresses don't match")
    if len(exchangers) != len(exchanger_keys):
        raise ValueError("The number of exchangers & keys don't match")

    full_addresses = tuple(
        Address(addr=address, asset=asset)
        for address, asset in zip(addresses, assets)
    )
    exchanger_profiles = tuple(
        ExchangerProfile(xchanger=xchanger, authkey=key)
        for xchanger, key in zip(exchangers, exchanger_keys)
    )
    dump_profile(
        Profile(addresses=full_addresses, exchangers=exchanger_profiles)
    )


def balance(args: argparse.Namespace) -> None:
    assets = set(args.asset)

    try:
        profile = load_profile()
    except FileNotFoundError:
        log.error(
            "profile not found, make sure to call `init` before invoking this"
        )
        raise

    addresses = tuple(
        address for address in profile.addresses if address.asset in assets
    )

    for address in addresses:
        print(
            ASSET_TO_REPOSITORY[address.asset](
                address=address.addr
            ).get_balance()
        )


def exchanger(args: argparse.Namespace) -> None:
    exchangers = set(args.exchanger_name)

    try:
        profile = load_profile()
    except FileNotFoundError:
        log.error(
            "profile not found, make sure to call `init` before invoking this"
        )
        raise
    exchanger_profiles = tuple(
        exchanger_profile
        for exchanger_profile in profile.exchangers
        if exchanger_profile.xchanger in exchangers
    )
    for xchanger_profile in exchanger_profiles:
        repository = EXCHANGER_TO_REPO[xchanger_profile.xchanger](
            xchanger_profile.authkey
        )
        print(repository.get_balances())
        print(repository.get_open_orders())
        print(repository.get_trades())


def transactions(args: argparse.Namespace) -> None:
    assets = args.asset

    try:
        profile = load_profile()
    except FileNotFoundError:
        log.error(
            "profile not found, make sure to call `init` before invoking this"
        )
        raise
    addresses = tuple(
        address for address in profile.addresses if address.asset in assets
    )

    for address in addresses:
        repo = ASSET_TO_REPOSITORY[address.asset](address=address.addr)
        print(repo.get_transactions())
        print(repo.scan_transfers_and_swaps())


def parse_args():
    parser = argparse.ArgumentParser(
        description="Monitor crypto wallets & exchangers", add_help=False
    )

    subparser = parser.add_subparsers(title="subcommands", dest="subcommands")

    init_parser = subparser.add_parser(
        "init",
        help="Init accounts",
    )
    init_parser.add_argument(
        "-a",
        "--asset",
        nargs="+",
        type=Asset,
        help="Specify the asset names",
        choices=list(CRYPTO_ASSETS),
    )
    init_parser.add_argument(
        "-d",
        "--address",
        nargs="+",
        help="BTC crypto wallet address (accepts more than one)",
    )
    init_parser.add_argument(
        "-n",
        "--exchanger-name",
        help="Remote exchanger service",
        type=lambda s: Exchanger(s.upper()),
        nargs="+",
        choices=list(Exchanger),
    )
    init_parser.add_argument(
        "-k",
        "--exchanger-key",
        help="Remote exchanger key",
        nargs="+",
    )
    init_parser.set_defaults(func=init)

    balance_parser = subparser.add_parser("balance", help="Fetch Balance")
    balance_parser.add_argument(
        "-a",
        "--asset",
        nargs="+",
        type=Asset,
        help="Specify the asset names",
        choices=list(CRYPTO_ASSETS),
    )
    balance_parser.set_defaults(func=balance)

    transactions_parser = subparser.add_parser(
        "transactions", help="Fetch Transactions"
    )
    transactions_parser.add_argument(
        "-a",
        "--asset",
        nargs="+",
        type=Asset,
        help="Specify the asset names",
        choices=[Asset.ETH],
    )
    transactions_parser.set_defaults(func=transactions)

    exchanger_parser = subparser.add_parser("exchanger", help="Query Exchanger")
    exchanger_parser.add_argument(
        "-n",
        "--exchanger-name",
        help="Remote exchanger service",
        type=lambda s: Exchanger(s.upper()),
        nargs="+",
        choices=list(Exchanger),
    )
    exchanger_parser.set_defaults(func=exchanger)
    return parser.parse_args()


# TODO: Improve output format
args = parse_args()
args.func(args)
