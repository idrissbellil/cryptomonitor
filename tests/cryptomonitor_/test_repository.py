import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

from cryptomonitor import model
from cryptomonitor.model import Asset, Balance
from cryptomonitor.repository import (
    BTCRepository,
    dump_profile,
    ETHRepository,
    KrakenRepository,
    load_profile,
)


class ProfilePersistenceTest(TestCase):
    def test_when_a_profile_is_dump_then_restored_then_it_succeeds(self):
        xprofile = model.ExchangerProfile(
            authkey="xxx", xchanger=model.Exchanger.KRAKEN
        )
        adr = model.Address(addr="yyy", asset=model.Asset.BTC)
        profile = model.Profile(addresses=(adr,), exchangers=(xprofile,))

        file_name = "/tmp/1111.yaml"
        dump_profile(profile, file_name)
        loaded_profile = load_profile(file_name)

        self.assertEqual(profile, loaded_profile)


class ETHRepositoryTest(TestCase):
    def setUp(self):
        self.subject = ETHRepository(
            "0xEf45F1460E535c3Cb20e23BABe8aDaf2519Ea5B3"
        )

    def test_when_balance_is_checked_then_it_returns(self):
        self.assertEqual(
            Balance(asset=Asset.ETH, amount=0), self.subject.get_balance()
        )

    def test_when_transactions_is_checked_then_it_returns(self):
        self.assertEqual(0, self.subject.get_transactions())


class BTCRepositoryTest(TestCase):
    def setUp(self):
        self.subject = BTCRepository("32xTLE3E1QkgDRPgncvNMhf4x7LHMAvkC9")

    def test_when_balance_is_checked_then_it_returns(self):
        self.assertEqual(
            Balance(asset=Asset.BTC, amount=0), self.subject.get_balance()
        )


class KrakenRepositoryTest(TestCase):
    def setUp(self):
        api_key = os.environ.get("API_KEY_KRAKEN")
        api_sec = os.environ.get("API_SEC_KRAKEN")

        assert api_key is not None, "Kraken API KEY is not setup as an env var"
        assert api_sec is not None, "Kraken API SEC is not setup as an env var"
        self.subject = KrakenRepository(f"{api_key} {api_sec}")

    def test_when_getting_balances_then_they_are_returned(self):
        with patch("cryptomonitor.repository.requests") as req:
            resp = MagicMock()
            req.post.return_value = resp
            resp.json.return_value = {
                "error": [],
                "result": {
                    "USD": "171288.6158",
                    "EUR": "504861.8946",
                    "BTC": "459567.9171",
                    "ETH": "500000.0000",
                },
            }
            self.assertEqual(
                (
                    Balance(asset=Asset.USD, amount=171288.6158),
                    Balance(asset=Asset.EUR, amount=504861.8946),
                    Balance(asset=Asset.BTC, amount=459567.9171),
                    Balance(asset=Asset.ETH, amount=500000.0000),
                ),
                self.subject.get_balances(),
            )

    def test_when_getting_open_orders_then_they_are_returned(self):
        with patch("cryptomonitor.repository.requests") as req:
            resp = MagicMock()
            req.post.return_value = resp
            resp.json.return_value = {
                "error": [],
                "result": {
                    "open": {},
                },
            }
            self.assertEqual({}, self.subject.get_open_orders())

    def test_when_getting_trades_then_they_are_returned(self):
        with patch("cryptomonitor.repository.requests") as req:
            resp = MagicMock()
            req.post.return_value = resp
            resp.json.return_value = {
                "error": [],
                "result": {
                    "trades": {},
                },
            }
            self.assertEqual({}, self.subject.get_trades())
