# CLI Crypto Monitor

## Example Usage

* Create a virtualenv and Install `requirements.txt`

```bash
(cryptomonitor) ➜  cryptomonitor git:(main) ✗ python -m cryptomonitor init -a ETH BTC -d 0xEf45F1460E535c3Cb20e23BABe8aDaf2519Ea5B3 32xTLE3E1QkgDRPgncvNMhf4x7LHMAvkC9 -n Kraken -k '<key> <private-key>'

(cryptomonitor) ➜  cryptomonitor git:(main) ✗ python -m cryptomonitor exchanger -n KRAKEN
()
{}
{}

(cryptomonitor) ➜  cryptomonitor git:(main) ✗ python -m cryptomonitor balance -a BTC     
Balance(asset=<Asset.BTC: 'BTC'>, amount=0)

(cryptomonitor) ➜  cryptomonitor git:(main) ✗ python -m cryptomonitor balance -a ETH
Balance(asset=<Asset.ETH: 'ETH'>, amount=0)

(cryptomonitor) ➜  cryptomonitor git:(main) ✗ python -m cryptomonitor transactions -a BTC
usage: __main__.py transactions [-h] [-a {Asset.ETH} [{Asset.ETH} ...]]
__main__.py transactions: error: argument -a/--asset: invalid choice: <Asset.BTC: 'BTC'> (choose from <Asset.ETH: 'ETH'>)

(cryptomonitor) ➜  cryptomonitor git:(main) ✗ python -m cryptomonitor transactions -a ETH
0
None
```

## Testing

* Setup the two env vars `API_KEY_KRAKEN` and `API_SEC_KRAKEN`.
* `pip install -r requirements-dev.txt`
* `coverage run -m unittest discover && coverage report`

## Roadmap

This was created in the beginning to satisfy some weird requirements as a 24h project, it will be updated/changed to:

* [ ] Drop the CLI and provide a library only access
* [ ] Have fully functional exchanger interface (focus on Binance for now)
* [ ] Drop ETH & add LTC & XRP
* [ ] Provide an interface in a separate repository (a Telegram bot for now)

It will be continued in [gitlab](gitlab.com/idrissbellil/cryptomonitor).
