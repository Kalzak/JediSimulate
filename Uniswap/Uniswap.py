from web3 import Web3
from eth_account import Account

private_key = "0xcd59762700e2c5bd1e677a4b289e460d498c447508104726bbf927e16afa5133"
local_eth_url = "http://localhost:31337"

class UniswapPool:

    def __init__(self, init_interaction):
        self.w3 = Web3(Web3.HTTPProvider(local_eth_url))
        self.account = Account.from_key(private_key)