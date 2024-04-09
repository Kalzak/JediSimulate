
import subprocess
import re
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.cairo.felt import encode_shortstring
from starknet_py.common import create_casm_class, create_sierra_compiled_contract
from starknet_py.hash.casm_class_hash import compute_casm_class_hash
from starknet_py.contract import Contract
from starknet_py.net.udc_deployer.deployer import Deployer

class JediswapPool:

    def __init__(self, init_interaction):
        # Create the address register structure
        self.address_register = {}
        self.account_classhash = None
        self.admin_account = None
        self.pool = None
        self.token0 = None
        self.token1 = None
        self.factory = None
        self.token_A = None
        self.token_B = None
        self.account_sierra_path = None

        self.client = FullNodeClient(node_url="http://0.0.0.0:5050")
        self.account = Account(
            client=self.client,
            address=0x733f6b834ece1b8b0427c12e1d3a5f38110156752e9c1bb6637852dbf167549,
            key_pair=KeyPair(
                private_key=0x259d4fd8f1a476f2b8f39e18e5522f85, 
                public_key=0x20cdbc421beaf586bed117b29b2d4644d04ebcc73cba1f97a27f625929b879d),
            chain=0x534e5f5345504f4c4941, # Spolia chain id
        )

        factory_sierra_path = 'Jediswap/PoolUtils/target/dev/jediswap_JediSwapV2Factory.contract_class.json'
        factory_casm_path = 'Jediswap/PoolUtils/target/dev/jediswap_JediSwapV2Factory.compiled_contract_class.json'
        pool_sierra_path = 'Jediswap/PoolUtils/target/dev/jediswap_JediSwapV2Pool.contract_class.json'
        pool_casm_path = 'Jediswap/PoolUtils/target/dev/jediswap_JediSwapV2Pool.compiled_contract_class.json'
        erc20_sierra_path = 'Jediswap/PoolUtils/target/dev/jediswap_ERC20.contract_class.json'
        erc20_casm_path = 'Jediswap/PoolUtils/target/dev/jediswap_ERC20.compiled_contract_class.json'
        account_sierra_path = 'Jediswap/PoolUtils/target/dev/jediswap_JediSwapV2Account.contract_class.json'
        account_casm_path = 'Jediswap/PoolUtils/target/dev/jediswap_JediSwapV2Account.compiled_contract_class.json'

        self.account_sierra_path = account_sierra_path

        ###### ERC20 #######
        erc20_class_hash = self._declare_contract(
            path_to_sierra=erc20_sierra_path,
            path_to_casm=erc20_casm_path
        )
        # erc20_class_hash = "0x02d3b48df6a7d005ecb44ba1a811bca2402a469d63e65c6b8bd1ea926d5b26a3"

        ###### TOKEN_A DEPLOYEMENT
        token_a_constructor_arguments = [
            encode_shortstring('TOKEN_A'),
            encode_shortstring('TOKEN_A'),
            1,
            '0x1'
        ]
        token_a_contract = self._deploy_contract(erc20_sierra_path, erc20_class_hash, token_a_constructor_arguments, 6)
        self.token_A = token_a_contract

        ####### TOKEN_B DEPLOYEMENT
        token_b_constructor_arguments = [
            encode_shortstring('TOKEN_B'),
            encode_shortstring('TOKEN_B'),
            1,
            '0x1'
        ]
        token_b_contract = self._deploy_contract(erc20_sierra_path, erc20_class_hash, token_b_constructor_arguments, 6)
        self.token_B = token_b_contract

        if token_a_contract < token_b_contract:
            self.token0 = token_a_contract
            self.token1 = token_b_contract
        else:
            self.token0 = token_b_contract
            self.token1 = token_a_contract
        print(f"Tokens: {self.token0}, {self.token1}")

        ###### POOL #######
        pool_class_hash = self._declare_contract(
            path_to_sierra=pool_sierra_path,
            path_to_casm=pool_casm_path
        )

        ###### FACTORY #######
        factory_class_hash = self._declare_contract(
            path_to_sierra=factory_sierra_path,
            path_to_casm=factory_casm_path
        )

        factory_constructor_arguments = [
            '0x1',
            pool_class_hash
        ]

        factory_contract = self._deploy_contract(factory_sierra_path, factory_class_hash, factory_constructor_arguments, 6)
        self.factory = factory_contract

        ##############################
        ## CREATE POOL FROM FACTORY
        ##############################

        pool_fee = init_interaction["data"]["deploy_data"]["fee"]

        self._tx_invoke(
            to=factory_contract,
            func='create_pool',
            calldata=[self.token0, self.token1, pool_fee]
        )

        pool_contract = self._tx_call(
            to=factory_contract,
            func='get_pool',
            calldata=[self.token0, self.token1, pool_fee]
        )[0]
        self.pool = pool_contract

        sqrt_arg = init_interaction["data"]["initialize_data"]["sqrt_price_x96"]

        self._tx_invoke(
            to=pool_contract,
            func='initialize',
            calldata=[sqrt_arg]
        )

        account_class_hash = self._declare_contract(
            path_to_sierra=account_sierra_path,
            path_to_casm=account_casm_path
        )
        self.account_classhash = account_class_hash

    def collect(self, interaction):
        caller = self._register_user(interaction["caller"])
        recipient = self._register_user(interaction["data"]["recipient"])
        tick_lower = interaction["data"]["tick_lower"]
        tick_upper = interaction["data"]["tick_upper"]
        amount_0_requested = interaction["data"]["amount_0_requested"]
        amount_1_requested = interaction["data"]["amount_1_requested"]

        tick_lower_sign = tick_lower < 0
        tick_upper_sign = tick_upper < 0

        # Execute the call
        status = None
        reason = None
        calldata = [recipient, {"mag": abs(tick_lower), "sign": tick_lower_sign}, {"mag": abs(tick_upper), "sign": tick_upper_sign}, amount_0_requested, amount_1_requested]

        try:
            self._tx_invoke(
                caller,
                "collect",
                calldata
            )
            status = "success"
        except Exception as e:
            reason = str(e)
            status = "reverted"
        
        return status, reason

    def burn(self, interaction):
        caller = self._register_user(interaction["caller"])
        tick_lower = interaction["data"]["tick_lower"]
        tick_upper = interaction["data"]["tick_upper"]
        amount = interaction["data"]["amount"]

        tick_lower_sign = tick_lower < 0
        tick_upper_sign = tick_upper < 0

        # Execute the call
        status = None
        reason = None
        calldata = [{"mag": abs(tick_lower), "sign": tick_lower_sign}, {"mag": abs(tick_upper), "sign": tick_upper_sign}, amount]
        try:
            self._tx_invoke(
                caller,
                "burn",
                calldata
            )
            status = "success"
        except Exception as e:
            reason = str(e)
            status = "reverted"
        
        return status, reason

    def mint(self, interaction):
        caller = self._register_user(interaction["caller"])
        recipient = self._register_user(interaction["data"]["recipient"])

        # Mint the necessary amount of tokens for liquidity provision
        t0_amt = interaction["other"]["amount0"]
        t1_amt = interaction["other"]["amount1"]
        self._mint_tokens(caller, self.token0, t0_amt)
        self._mint_tokens(caller, self.token1, t1_amt)

        # Extract data to more readable variables
        tick_lower = interaction["data"]["tick_lower"]
        tick_upper = interaction["data"]["tick_upper"]
        amount = interaction["data"]["amount"]
        data = interaction["data"]["data"]

        tick_lower_sign = tick_lower < 0
        tick_upper_sign = tick_upper < 0

        # Execute the call
        status = None
        reason = None
        calldata = [recipient, {"mag": abs(tick_lower), "sign": tick_lower_sign}, {"mag": abs(tick_upper), "sign": tick_upper_sign}, amount, []]
        try:
            self._tx_invoke(
                caller,
                "mint",
                calldata
            )
            status = "success"
        except Exception as e:
            reason = str(e)
            status = "reverted"
        
        return status, reason

    def swap(self, interaction):
        # Register the caller and recipient
        caller = self._register_user(interaction["caller"])
        recipient = self._register_user(interaction["data"]["recipient"])

        # Mint the necessary amount of tokens for swap
        t0_amt = interaction["other"]["amount0"]
        t1_amt = interaction["other"]["amount1"]
        if t0_amt > 0:
            self._mint_tokens(caller, self.token0, t0_amt)

        if t1_amt > 0:
            self._mint_tokens(caller, self.token1, t1_amt)

        zero_for_one = interaction["data"]["zero_for_one"]
        amount_specified = interaction["data"]["amount_specified"]
        sqrt_price_limit_x96 = interaction["data"]["sqrt_price_limit_x96"]
        amount_specified_sign = amount_specified < 0

        # Execute the call
        status = None
        reason = None
        calldata = [recipient, zero_for_one, {"mag": abs(amount_specified), "sign": amount_specified_sign}, sqrt_price_limit_x96, []]
        try:
            self._tx_invoke(
                caller,
                "swap",
                calldata
            )
            status = "success"
        except Exception as e:
            reason = str(e)
            status = "reverted"
        
        return status, reason
    
    def get_position(self, owner, tick_lower, tick_upper):
        jedi_owner = self.address_register[str(owner)]
        tick_lower_sign = tick_lower < 0
        tick_upper_sign = tick_upper < 0
        position_info = self._tx_call(
            to=self.pool,
            func='get_position_info',
            calldata=[{"owner": jedi_owner, "tick_lower": {"mag": abs(tick_lower), "sign": tick_lower_sign}, "tick_upper": {"mag": abs(tick_upper),  "sign": tick_upper_sign}}]
        )
        position_info = [
            # liquidity: u128
            position_info[0]['liquidity'],
            # fee_growth_inside_0_last_X128: u256
            position_info[0]['fee_growth_inside_0_last_X128'],
            # fee_growth_inside_1_last_X128: u256
            position_info[0]['fee_growth_inside_1_last_X128'],
            # tokens_owed_0: u128
            position_info[0]['tokens_owed_0'],
            # tokens_owed_1: u128
            position_info[0]['tokens_owed_1'],
        ]
        return position_info
    
    def get_sqrt_price_X96(self):
        sqrt_price_X96_data = self._tx_call(
            to=self.pool,
            func='get_sqrt_price_X96',
            calldata=[]
        )
        return sqrt_price_X96_data[0]
    
    def get_tick(self):
        tick_data = self._tx_call(
            to=self.pool,
            func='get_tick',
            calldata=[]
        )
        # print(f"tick data - {tick_data}")
        tick_sign = -1 if tick_data[0]['sign'] else 1
        tick = tick_data[0]['mag'] * tick_sign
        return tick
    
    def get_fee_growth_global_0_X128(self):
        fee_growth_global_0_X128_data = self._tx_call(
            to=self.pool,
            func='get_fee_growth_global_0_X128',
            calldata=[]
        )
        # fee_growth_global_0_X128 = int(fee_growth_global_0_X128_data[0], 16) + (int(fee_growth_global_0_X128_data[1], 16)*2**128)
        return fee_growth_global_0_X128_data[0]
    
    def get_fee_growth_global_1_X128(self):
        fee_growth_global_1_X128_data = self._tx_call(
            to=self.pool,
            func='get_fee_growth_global_1_X128',
            calldata=[]
        )
        # fee_growth_global_1_X128 = int(fee_growth_global_1_X128_data[0], 16) + (int(fee_growth_global_1_X128_data[1], 16)*2**128)
        return fee_growth_global_1_X128_data[0]

    def get_liquidity(self):
        liquidity = self._tx_call(
            to=self.pool,
            func='get_liquidity',
            calldata=[]
        )
        return liquidity[0]
    
    def get_token_balance(self, token_addr, address):
        if token_addr != self.token0 and token_addr != self.token1:
            print("get_token_balance: invalid token address")
            exit(0) 

        jedi_address = self.address_register[str(address)]
        balance = self._tx_call(
            to=token_addr,
            func='balance_of',
            calldata=[jedi_address]
        )
        return balance[0]
    
    def get_token0(self):
        return self.token0
    
    def get_token1(self):
        return self.token1
    
    def _register_user(self, address):
        if address in self.address_register.keys():
            return self.address_register[address]
        new_user = self._deploy_contract(
            self.account_sierra_path,
            self.account_classhash, 
            [self.pool, self.token0, self.token1],
            len(self.address_register)
        )
        self.address_register[address] = new_user

        return new_user

    def _mint_tokens(self, recipient, token, amount):
        return self._tx_invoke(
            token,
            "mint",
            calldata=[recipient, amount]
        )
    
    def _declare_contract(self, path_to_sierra, path_to_casm):
        # print('declaring')
        compiled_contract = self._get_contract(path_to_sierra)
        casm_compiled_contract = self._get_contract(path_to_casm)
        casm_class = create_casm_class(casm_compiled_contract)
        casm_class_hash = compute_casm_class_hash(casm_class)
        declare_result = Contract.declare_v2_sync(
            account=self.account, compiled_contract=compiled_contract, 
            compiled_class_hash=casm_class_hash,max_fee=int(1e18)
        )
        declare_result.wait_for_acceptance_sync()
        return declare_result.class_hash

    def _deploy_contract(self, path_to_sierra, class_hash, constructor_arguments, salt):
        # print('deploying')
        compiled_contract = self._get_contract(path_to_sierra)
        abi = create_sierra_compiled_contract(compiled_contract=compiled_contract).parsed_abi
        
        deployer = Deployer()

        contract_deployment = deployer.create_contract_deployment(
            class_hash=class_hash,
            abi=abi,
            cairo_version=1,
            calldata=constructor_arguments,
            salt=salt,
        )

        res = self.account.execute_v1_sync(calls=contract_deployment.call, max_fee=int(1e16))
        self.client.wait_for_tx_sync(res.transaction_hash)
        return contract_deployment.address

    def _tx_invoke(self, to, func, calldata):
        # print(f"invoking - {to}, {func}, {calldata}")
        contract = Contract.from_address_sync(provider=self.account, address=to)
        invocation = contract.functions[func].invoke_v1_sync(*calldata, max_fee=int(1e16))
        invocation.wait_for_acceptance_sync()

    def _tx_call(self, to, func, calldata):
        # print(f"calling - {to}, {func}, {calldata}")
        contract = Contract.from_address_sync(provider=self.account, address=to)
        result = contract.functions[func].call_sync(*calldata)
        return result

    def _split_u256(self, number):
        return (number % 2**128, number // 2**128)
    
    def _u256_to_int(self, lower, upper):
        return (int(lower, 16) + (int(upper, 16) << 128))

    def _get_contract(self, file_path):
        with open(file_path, 'r') as f:
            text=f.read()  
        return text
