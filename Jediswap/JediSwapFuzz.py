
import subprocess
import re

class JSF:

    def __init__(self):
        self.fuzz_contract = None

        fuzz_sierra_path = 'Jediswap/PoolUtils/target/dev/jediswap_JediSwapFuzz.contract_class.json'
        fuzz_casm_path = 'Jediswap/PoolUtils/target/dev/jediswap_JediSwapFuzz.compiled_contract_class.json'

        ###### ERC20 #######
        fuzz_class_hash = self._declare_contract(
            path_to_sierra=fuzz_sierra_path,
            path_to_casm=fuzz_casm_path
        )
        fuzz_contract, _ = self._deploy_contract(fuzz_class_hash, [])
        self.fuzz_contract = fuzz_contract

        self.add_i8 = self._create_math_func('add', 8, True)
        self.add_i16 = self._create_math_func('add', 16, True)
        self.add_i32 = self._create_math_func('add', 32, True)
        self.add_i128 = self._create_math_func('add', 128, True)
        self.add_i256 = self._create_math_func('add', 256, True)


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
        res = re.findall(r'".*"', result)
        output = []
        for x in res:
            output.append(x[1:-1])
        return output
    
    def _create_math_func(self, operation_name, num_type, signed):
        sign_i = 'i' if signed else 'u'
        if sign_i:
            def handle_output(output, is_first_string):
                result_sign = 1 if int(output[1], 16) == 0 else -1
                if is_first_string:
                    return int(output[0], 16) * result_sign
                else:
                    return output[0] * result_sign
                
        else:
            def handle_output(output, is_first_string):
                if is_first_string:
                    return int(output[0], 16)
                else:
                    return output[0]

        if num_type != 256:
            def func_to_return(num1, num2):
                num1_sign = int(num1 < 0)
                num2_sign = int(num2 < 0)
                res = self._tx_call(
                    to=self.fuzz_contract,
                    func=f'{operation_name}_{sign_i}{str(num_type)}',
                    calldata=[
                        str(abs(num1)), str(num1_sign),
                        str(abs(num2)), str(num2_sign)
                    ]
                )
                result = handle_output(res, True)
                return result
        
        else:
            def func_to_return(num1, num2):
                num1_sign = int(num1 < 0)
                num2_sign = int(num2 < 0)
                num1_low, num1_high = _split_u256(abs(num1))
                num2_low, num2_high = _split_u256(abs(num2))
                res = self._tx_call(
                    to=self.fuzz_contract,
                    func=f'{operation_name}_{sign_i}{str(num_type)}',
                    calldata=[
                        str(num1_low), str(num1_high), str(num1_sign),
                        str(num2_low), str(num2_high), str(num2_sign),
                    ]
                )
                number = int(res[0], 16) + (int(res[1], 16)*2**128)
                res = [number, res[-1]]
                result = handle_output(res, False)

                return result

        return func_to_return

def _split_u256(number):
        return (number % 2**128, number // 2**128)
