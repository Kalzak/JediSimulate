import os
import json
from web3 import Web3
from eth_account import Account

private_key = "0xcd59762700e2c5bd1e677a4b289e460d498c447508104726bbf927e16afa5133"
local_eth_url = "http://localhost:31337"

class UniswapPool:

    def __init__(self, init_interaction):
        # Set up the web3 connection
        self.w3 = Web3(Web3.HTTPProvider(local_eth_url))
        self.account = Account.from_key(private_key)

        # Create the address register structure
        self.address_register = {}

        # Deploy pool factory
        factory_abi = load_abi("PoolUtils/out/UniswapV3Factory.sol/UniswapV3Factory.json")
        factory_bytecode = load_bytecode("PoolUtils/out/UniswapV3Factory.sol/UniswapV3Factory.json")
        factory_deployer = self.w3.eth.contract(abi=factory_abi, bytecode=factory_bytecode)
        tx_hash = factory_deployer.constructor().transact({"from": self.account.address})
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.factory = self.w3.eth.contract(address=tx_receipt.contractAddress, abi=factory_abi)

        # Deploy token0 and token1
        erc20_abi = load_abi("PoolUtils/out/MintableERC20.sol/MintableERC20.json")
        erc20_bytecode = load_bytecode("PoolUtils/out/MintableERC20.sol/MintableERC20.json")
        erc20_deployer = self.w3.eth.contract(abi=erc20_abi, bytecode=erc20_bytecode)
        tx_hash = erc20_deployer.constructor("AaBbCc", "ABC").transact({"from": self.account.address})
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.token0 = self.w3.eth.contract(address=tx_receipt.contractAddress, abi=erc20_abi)
        tx_hash = erc20_deployer.constructor("XxYyZz", "XYZ").transact({"from": self.account.address})
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.token1 = self.w3.eth.contract(address=tx_receipt.contractAddress, abi=erc20_abi)

        # Swap token0 and token1 to match pool if necessary
        if int(self.token0.address, 16) > int(self.token1.address, 16):
            self.token0, self.token1 = self.token1, self.token0

        # Create the pool
        pool_fee = init_interaction["data"]["deploy_data"]["fee"]
        tx_hash = self.factory.functions.createPool(self.token0.address, self.token1.address, pool_fee).transact({"from": self.account.address})
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Get the pool
        pool_address = self.factory.functions.getPool(self.token0.address, self.token1.address, pool_fee).call()
        pool_abi = load_abi("PoolUtils/out/UniswapV3Pool.sol/UniswapV3Pool.json")
        self.pool = self.w3.eth.contract(address=pool_address, abi=pool_abi)

        # Initialize the pool
        sqrt_arg = init_interaction["data"]["initialize_data"]["sqrt_price_x96"]
        tx_hash = self.pool.functions.initialize(sqrt_arg).transact({"from": self.account.address})
        self.w3.eth.wait_for_transaction_receipt(tx_hash)

    def register_user(self, address):
        # If already registered, return the user contract
        if address in self.address_register.keys():
            return self.address_register[address]
        # Otherwise deploy user contract
        user_contract_abi = load_abi("PoolUtils/out/UserContract.sol/UserContract.json")
        user_contract_bytecode = load_bytecode("PoolUtils/out/UserContract.sol/UserContract.json")
        user_contract_deployer = self.w3.eth.contract(abi=user_contract_abi, bytecode=user_contract_bytecode)
        tx_hash = user_contract_deployer.constructor(
            self.pool.address,
            self.token0.address,
            self.token1.address
        ).transact({"from": self.account.address})
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        new_user = self.w3.eth.contract(address=tx_receipt.contractAddress, abi=user_contract_abi)
        self.address_register[address] = new_user
        return new_user

    def collect(self, interaction):
        # Register the caller and recipient
        caller = self.register_user(interaction["caller"])
        recipient = self.register_user(interaction["data"]["recipient"])

        # Extract the interaction data
        tick_lower = interaction["data"]["tick_lower"]
        tick_upper = interaction["data"]["tick_upper"]
        amount_0_requested = interaction["data"]["amount_0_requested"]
        amount_1_requested = interaction["data"]["amount_1_requested"]

        # Execute the call
        status = None
        reason = None
        try:
            tx_hash = caller.functions.collect(
                recipient.address,
                tick_lower,
                tick_upper,
                amount_0_requested,
                amount_1_requested
            ).transact({"from": self.account.address})
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = "success"
        except Exception as e:
            reason = str(e)
            status = "reverted"

        return status, reason

    def burn(self, interaction):
        # Register the caller
        caller = self.register_user(interaction["caller"])

        # Extract the interaction data
        tick_lower = interaction["data"]["tick_lower"]
        tick_upper = interaction["data"]["tick_upper"]
        amount = interaction["data"]["amount"]

        # Execute the call
        status = None
        reason = None
        try:
            tx_hash = caller.functions.burn(
                tick_lower,
                tick_upper,
                amount
            ).transact({"from": self.account.address})
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = "success"
        except Exception as e:
            reason = str(e)
            status = "reverted"

        return status, reason


    def mint(self, interaction):
        # Register the caller and recipient
        caller = self.register_user(interaction["caller"])
        recipient = self.register_user(interaction["data"]["recipient"])

        # Mint necessary amount of tokens
        t0_amt = interaction["other"]["amount0"]
        t1_amt = interaction["other"]["amount1"]
        self._mint_tokens(self.token0, recipient.address, t0_amt)
        self._mint_tokens(self.token1, recipient.address, t1_amt)

        # Extract the interaction data
        tick_lower = interaction["data"]["tick_lower"]
        tick_upper = interaction["data"]["tick_upper"]
        amount = interaction["data"]["amount"]
        data = interaction["data"]["data"]

        # Execute the call
        status = None
        reason = None
        try:
            tx_hash = caller.functions.mint(
                recipient.address,
                tick_lower,
                tick_upper,
                amount,
                self.w3.to_bytes(0)
            ).transact({"from": self.account.address})
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = "success"
        except Exception as e:
            reason = str(e)
            status = "reverted"

        return status, reason

    def swap(self, interaction):
        # Register the caller and recipient
        caller = self.register_user(interaction["caller"])
        recipient = self.register_user(interaction["data"]["recipient"])

        # Mint necessary amount of tokens
        t0_amt = interaction["other"]["amount0"]
        t1_amt = interaction["other"]["amount1"]
        if t0_amt > 0:
            self._mint_tokens(self.token0, caller.address, t0_amt)
        if t1_amt > 0:
            self._mint_tokens(self.token1, caller.address, t1_amt)

        # Extract the interaction data
        zero_for_one = interaction["data"]["zero_for_one"]
        amount_specified = interaction["data"]["amount_specified"]
        sqrt_price_limit_x96 = interaction["data"]["sqrt_price_limit_x96"]
        data = self.w3.to_bytes(0)

        # Execute the call
        status = None
        reason = None
        try:
            tx_hash = caller.functions.swap(
                recipient.address,
                zero_for_one,
                amount_specified,
                sqrt_price_limit_x96,
                data
            ).transact({"from": self.account.address})
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = "success"
        except Exception as e:
            reason = str(e)
            status = "reverted"

        return status, reason
    
    def get_position(self, owner, tick_lower, tick_upper):
        uni_owner = self.register_user(owner)
        position_hash = self.w3.solidity_keccak(
            ["address", "int24", "int24"], 
            [uni_owner.address, tick_lower, tick_upper]
        )
        position_info = self.pool.functions.positions(position_hash).call()
        return position_info
    
    def get_tick(self):
        slot0 = self.pool.functions.slot0().call()
        return slot0[1]

    def get_sqrt_price_X96(self):
        slot0 = self.pool.functions.slot0().call()
        return slot0[0]
    
    def get_fee_growth_global_0_X128(self):
        fee_growth_global_0_X128 = self.pool.functions.feeGrowthGlobal0X128().call()
        return fee_growth_global_0_X128
    
    def get_fee_growth_global_1_X128(self):
        fee_growth_global_1_X128 = self.pool.functions.feeGrowthGlobal1X128().call()
        return fee_growth_global_1_X128
    
    def get_liquidity(self):
        liquidity = self.pool.functions.liquidity().call()
        return liquidity

    def get_token_balance(self, token_addr, address):
        anvil_addr = self.register_user(address).address
        if token_addr == self.token0.address:
            return self.token0.functions.balanceOf(anvil_addr).call()
        elif token_addr == self.token1.address:
            return self.token1.functions.balanceOf(anvil_addr).call()
        else:
            print("get_token_balance: invalid token address")


    def get_token0(self):
        return self.token0.address
    
    def get_token1(self):
        return self.token1.address

    def _mint_tokens(self, token, recipient, amount):
        tx_hash = token.functions.mint(recipient, amount).transact({"from": self.account.address})
        self.w3.eth.wait_for_transaction_receipt(tx_hash)

def load_bytecode(path):
    path = get_module_path() + "/" + path
    with open(path, "r") as file:
        contract_data = json.load(file)
        return contract_data["bytecode"]["object"]
    
def load_abi(path):
    path = get_module_path() + "/" + path
    with open(path, "r") as file:
        contract_data = json.load(file)
        return contract_data["abi"]

# Calculates the module path for loading files
def get_module_path():
    return os.path.dirname(os.path.realpath(__file__))