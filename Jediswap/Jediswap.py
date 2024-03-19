
import subprocess
import re

# jedi_caller = '0x517ececd29116499f4a1b64b094da79ba08dfd54a3edaa316134c41f8160973'


class JediswapPool:

    def __init__(self, init_interaction):
        # Create the address register structure
        self.address_register = {}
        self.account_classhash = None
        self.pool = None
        self.token0 = None
        self.token1 = None
        self.factory = None
        self.token_A = None
        self.token_B = None

        factory_sierra_path = 'Jediswap/PoolUtils/target/dev/jediswap_JediSwapV2Factory.contract_class.json'
        factory_casm_path = 'Jediswap/PoolUtils/target/dev/jediswap_JediSwapV2Factory.compiled_contract_class.json'
        pool_sierra_path = 'Jediswap/PoolUtils/target/dev/jediswap_JediSwapV2Pool.contract_class.json'
        pool_casm_path = 'Jediswap/PoolUtils/target/dev/jediswap_JediSwapV2Pool.compiled_contract_class.json'
        erc20_sierra_path = 'Jediswap/PoolUtils/target/dev/jediswap_ERC20.contract_class.json'
        erc20_casm_path = 'Jediswap/PoolUtils/target/dev/jediswap_ERC20.compiled_contract_class.json'
        account_sierra_path = 'Jediswap/PoolUtils/target/dev/jediswap_JediSwapV2Account.contract_class.json'
        account_casm_path = 'Jediswap/PoolUtils/target/dev/jediswap_JediSwapV2Account.compiled_contract_class.json'


        ###### ACCOUNT #######
        caller = '0x517ececd29116499f4a1b64b094da79ba08dfd54a3edaa316134c41f8160973'

        ###### ERC20 #######
        erc20_class_hash = self._declare_contract(
            path_to_sierra=erc20_sierra_path,
            path_to_casm=erc20_casm_path
        )

        ###### TOKEN_A DEPLOYEMENT
        token_a_constructor_arguments = [
            self._get_str_to_felt('TOKEN_A'),
            self._get_str_to_felt('TOKEN_A'),
            f'u256:{2**250}',
            caller
        ]
        token_a_contract, _ = self._deploy_contract(erc20_class_hash, token_a_constructor_arguments)
        self.token_A = token_a_contract

        ####### TOKEN_B DEPLOYEMENT
        token_b_constructor_arguments = [
            self._get_str_to_felt('TOKEN_B'),
            self._get_str_to_felt('TOKEN_B'),
            f'u256:{2**250}',
            caller
        ]
        token_b_contract, _ = self._deploy_contract(erc20_class_hash, token_b_constructor_arguments)
        self.token_B = token_b_contract

        if int(token_a_contract, 16) < int(token_b_contract, 16):
            self.token0 = token_a_contract
            self.token1 = token_b_contract
        else:
            self.token0 = token_b_contract
            self.token1 = token_a_contract

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
            caller,
            pool_class_hash
        ]

        factory_contract, _ = self._deploy_contract(factory_class_hash, factory_constructor_arguments)
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

        sqrt_low, sqrt_high = self._split_u256(sqrt_arg)

        self._tx_invoke(
            to=pool_contract,
            func='initialize',
            calldata=[f'{sqrt_low}', f'{sqrt_high}']
        )

        account_class_hash = self._declare_contract(
            path_to_sierra=account_sierra_path,
            path_to_casm=account_casm_path
        )
        self.account_classhash = account_class_hash
        print(f'''
Jediswap addresses:
FACTORY: {factory_contract}
POOL:    {pool_contract}
TOKEN_A: {token_a_contract}
TOKEN_B: {token_b_contract}
TOKEN_0: {self.token0}
TOKEN_1: {self.token1}
''')
    
    def collect(self, interaction):
        caller, _ = self._register_user(interaction["caller"])
        recipient, _ = self._register_user(interaction["data"]["recipient"])
        tick_lower = interaction["data"]["tick_lower"]
        tick_upper = interaction["data"]["tick_upper"]
        amount_0_requested = interaction["data"]["amount_0_requested"]
        amount_1_requested = interaction["data"]["amount_1_requested"]

        print(
        f'''
COLLECT JEDI
Recipient:                 {recipient}
Tick Lower:                {tick_lower}
Tick Upper:                {tick_upper}
Amount 0 Requested:        {amount_0_requested}
Amount 1 Requested:        {amount_1_requested}
            '''
        )


        tick_lower_sign = int(tick_lower < 0)
        tick_upper_sign = int(tick_upper < 0)

        # Execute the call
        status = None
        reason = None

        try:
            tx_hash = self._tx_invoke(
                caller,
                "collect",
                [
                    str(recipient), str(abs(tick_lower)), str(tick_lower_sign), str(abs(tick_upper)), str(tick_upper_sign), 
                    str(amount_0_requested), str(amount_1_requested)
                ]
            )
            status = "success"
        except Exception as e:
            reason = str(e)
            status = "reverted"
        
        return status, reason, tx_hash

    def burn(self, interaction):
        caller, _ = self._register_user(interaction["caller"])
        tick_lower = interaction["data"]["tick_lower"]
        tick_upper = interaction["data"]["tick_upper"]
        amount = interaction["data"]["amount"]

        print(
        f'''
BURN JEDI
Tick Lower:    {tick_lower}
Tick Upper:    {tick_upper}
Amount:        {amount}
            '''
        )

        tick_lower_sign = int(tick_lower < 0)
        tick_upper_sign = int(tick_upper < 0)

        # Execute the call
        status = None
        reason = None
        try:
            tx_hash = self._tx_invoke(
                caller,
                "burn",
                [str(abs(tick_lower)), str(tick_lower_sign), str(abs(tick_upper)), str(tick_upper_sign), str(amount)]
            )
            status = "success"
        except Exception as e:
            reason = str(e)
            status = "reverted"
        
        return status, reason, tx_hash

    def mint(self, interaction):
        caller, _ = self._register_user(interaction["caller"])
        recipient, _ = self._register_user(interaction["data"]["recipient"])

        # Mint the necessary amount of tokens for liquidity provision
        t0_amt = interaction["other"]["amount0"]
        t1_amt = interaction["other"]["amount1"]
        t0_amt_low, t0_amt_high = self._split_u256(t0_amt)
        t1_amt_low, t1_amt_high = self._split_u256(t1_amt)
        self._mint_tokens(caller, self.token0, t0_amt_low, t0_amt_high)
        self._mint_tokens(caller, self.token1, t1_amt_low, t1_amt_high)

        # Extract data to more readable variables
        tick_lower = interaction["data"]["tick_lower"]
        tick_upper = interaction["data"]["tick_upper"]
        amount = interaction["data"]["amount"]
        data = interaction["data"]["data"]

        print(
        f'''
MINT JEDI
Recipient:     {recipient}
Tick Lower:    {tick_lower}
Tick Upper:    {tick_upper}
Amount:        {amount}
Data:          {0}
Token0 amount: {t0_amt}
Token1 amount: {t1_amt}
            '''
        )
        tick_lower_sign = int(tick_lower < 0)
        tick_upper_sign = int(tick_upper < 0)

        # Execute the call
        status = None
        reason = None
        try:
            tx_hash = self._tx_invoke(
                caller,
                "mint",
                [str(recipient), str(abs(tick_lower)), str(tick_lower_sign), 
                str(abs(tick_upper)), str(tick_upper_sign), str(amount), str(0)]
            )
            status = "success"
        except Exception as e:
            reason = str(e)
            status = "reverted"
        
        return status, reason, tx_hash

    def swap(self, interaction):
        # Register the caller and recipient
        caller, _ = self._register_user(interaction["caller"])
        recipient, _ = self._register_user(interaction["data"]["recipient"])

        # Mint the necessary amount of tokens for swap
        t0_amt = interaction["other"]["amount0"]
        t1_amt = interaction["other"]["amount1"]
        if t0_amt > 0:
            t0_amt_low, t0_amt_high = self._split_u256(t0_amt)
            self._mint_tokens(caller, self.token0, t0_amt_low, t0_amt_high)

        if t1_amt > 0:
            t1_amt_low, t1_amt_high = self._split_u256(t1_amt)
            self._mint_tokens(caller, self.token1, t1_amt_low, t1_amt_high)

        zero_for_one = interaction["data"]["zero_for_one"]
        amount_specified = interaction["data"]["amount_specified"]
        sqrt_price_limit_x96 = interaction["data"]["sqrt_price_limit_x96"]
        data = 0
        amount_specified_sign = int(amount_specified < 0)
        amount_specified_low, amount_specified_high = self._split_u256(abs(amount_specified))
        sqrt_price_limit_x96_low, sqrt_price_limit_x96_high = self._split_u256(abs(sqrt_price_limit_x96))

        print(
        f'''
SWAP JEDI
Recipient:            {recipient}
Zero for One:         {zero_for_one}
Amount Specified:     {amount_specified}
Sqrt Price Limit X96: {sqrt_price_limit_x96}
Data:                 {0}
            '''
        )

        # Execute the call
        status = None
        reason = None
        try:
            tx_hash = self._tx_invoke(
                caller,
                "swap",
                [str(recipient), str(int(zero_for_one)), str(amount_specified_low), str(amount_specified_high), str(amount_specified_sign),
                str(sqrt_price_limit_x96_low), str(sqrt_price_limit_x96_high), str(data)
                ]
            )
            status = "success"
        except Exception as e:
            reason = str(e)
            status = "reverted"
        
        return status, reason, tx_hash
    
    def get_position(self, owner, tick_lower, tick_upper):
        jedi_owner = self.address_register[str(owner)]
        tick_lower_sign = int(tick_lower < 0)
        tick_upper_sign = int(tick_upper < 0)
        position_info = self._tx_call(
            to=self.pool,
            func='get_position_info',
            calldata=[
                str(jedi_owner),
                str(abs(tick_lower)), str(tick_lower_sign),
                str(abs(tick_upper)), str(tick_upper_sign)
            ]
        )
        return position_info

    
    def _register_user(self, address):
        if address in self.address_register.keys():
            return self.address_register[address], None
        new_user, tx_hash_obj = self._deploy_contract(
            self.account_classhash, 
            [self.pool, self.token0, self.token1]
        )
        print("NEW JEDI USER:", new_user)
        self.address_register[address] = new_user

        return new_user, tx_hash_obj

    def _mint_tokens(self, recipient, token, amount_low, amount_high):
        return self._tx_invoke(
            token,
            "transfer",
            calldata=[recipient, amount_low, amount_high]
        )
    
    def _declare_contract(self, path_to_sierra, path_to_casm):
        declare_command = ['starkli', 'declare', 
                        '--casm-file', path_to_casm, path_to_sierra
                        ]
        result = subprocess.run(declare_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode().strip()

    def _deploy_contract(self, class_hash, constructor_arguments):
        deploy_command = [
            'starkli', 'deploy', class_hash, *constructor_arguments
        ]
        callresult = subprocess.run(deploy_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        contract_address = callresult.stdout.decode().strip()
        error = callresult.stderr.decode()
        if error.split()[0] == "Error:":
            print(f'''
                    DEPLOY TX ERROR:
                    class_hash:       {class_hash}
                    constructor data: {constructor_arguments}
                ''', error)
            exit(0)
        tx_output_data = error.split()
        tx_hash = tx_output_data[tx_output_data.index('transaction:') + 1]
        tx_hash_obj = {
            "tx_command": ["deploy", class_hash, *constructor_arguments],
            "tx_hash": tx_hash,

        }
        return contract_address, tx_hash_obj

    def _tx_invoke(self, to, func, calldata):
        calldata = [str(x) for x in calldata]
        invoke_command = [
            'starkli', 'invoke', to, func, *calldata
        ]
        callresult = subprocess.run(invoke_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        error = callresult.stderr.decode()
        if error.split()[0] == "Error:":
            print(f'''
                    INVOKE TX ERROR:
                    to:       {to}
                    function: {func}
                    calldata: {calldata}
                ''', error)
            exit(0)

        tx_hash_obj = {
            "tx_command": ["invoke", to, func, *calldata],
            "tx_hash": error.split()[-1],
        }
        return tx_hash_obj



    def _tx_call(self, to, func, calldata):
        calldata = [str(x) for x in calldata]
        deploy_command = [
            'starkli', 'call', to, func, *calldata
        ]
        callresult = subprocess.run(deploy_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = callresult.stdout.decode()
        error = callresult.stderr
        if len(error) > 0:
            print(f'''
                    CALL TX ERROR:
                    to:       {to}
                    function: {func}
                    calldata: {calldata}
                ''', error.decode())
            exit(0)
        # result = subprocess.run(deploy_command, stdout=subprocess.PIPE).stdout.decode()
        res = re.findall(r'".*"', result)
        output = []
        for x in res:
            output.append(x[1:-1])
        return output

    def _get_str_to_felt(self, string):
        get_name_in_felt_command = [
            'starkli', 'to-cairo-string', string
        ]
        result = subprocess.run(get_name_in_felt_command, stdout=subprocess.PIPE)
        return result.stdout.decode().strip()

    def _split_u256(self, number):
        return (number % 2**128, number // 2**128)

# def load_bytecode(path):
#     path = get_module_path() + "/" + path
#     with open(path, "r") as file:
#         contract_data = json.load(file)
#         return contract_data["bytecode"]["object"]
    
# def load_abi(path):
#     path = get_module_path() + "/" + path
#     with open(path, "r") as file:
#         contract_data = json.load(file)
#         return contract_data["abi"]

# # Calculates the module path for loading files
# def get_module_path():
#     return os.path.dirname(os.path.realpath(__file__))