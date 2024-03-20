from web3 import Web3
from eth_abi import decode
from Uniswap import load_abi
import json
import os

POOL_DEPLOYMENT_BLOCK = 12376729

#POOL_ADDRESS = "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640" # ETH-USDC
POOL_ADDRESS = "0x7858E59e0C01EA06Df3aF3D20aC7B0003275D4Bf" # USDC-USDT
ROUTER_ADDRESS = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
POSITION_MANAGER_ADDRESS = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"


def get_pool_interactions(w3, pool_data, blocknum):
    pool = pool_data["pool"]
    
    interactions = {}
    interactions_flattened = []

    initialize_logs = pool.events.Initialize().get_logs(fromBlock=blocknum, toBlock=blocknum)
    mint_logs = pool.events.Mint().get_logs(fromBlock=blocknum, toBlock=blocknum)
    burn_logs = pool.events.Burn().get_logs(fromBlock=blocknum, toBlock=blocknum)
    collect_logs = pool.events.Collect().get_logs(fromBlock=blocknum, toBlock=blocknum)
    swap_logs = pool.events.Swap().get_logs(fromBlock=blocknum, toBlock=blocknum)
    flash_logs = pool.events.Flash().get_logs(fromBlock=blocknum, toBlock=blocknum)
    #collect_protocol_logs = pool.events.CollectProtocol().get_logs(fromBlock=blocknum, toBlock=blocknum)

    process_logs(interactions, w3, initialize_logs, pool_data, blocknum, process_initialize_log)
    process_logs(interactions, w3, mint_logs, pool_data, blocknum, process_mint_log)
    process_logs(interactions, w3, burn_logs, pool_data, blocknum, process_burn_log)
    process_logs(interactions, w3, collect_logs, pool_data, blocknum, process_collect_log)
    process_logs(interactions, w3, swap_logs, pool_data, blocknum, process_swap_log)
    process_logs(interactions, w3, flash_logs, pool_data, blocknum, process_flash_log)

    for tx_idx in sorted(interactions.keys()):
        print(tx_idx)
        for log_idx in sorted(interactions[tx_idx].keys()):
            interactions_flattened.append(interactions[tx_idx][log_idx])

    return interactions_flattened

def process_logs(interactions, w3, logs, pool_data, blocknum, processor_func):
    # Exit early if no relevant logs
    if len(logs) == 0:
        return

    # Extract the data for each log
    for log in logs:
        tx_idx = log["transactionIndex"]
        log_idx = log["logIndex"]

        processed_log = processor_func(w3, log, pool_data, blocknum)

        if tx_idx not in interactions:
            interactions[tx_idx] = {}
        
        interactions[tx_idx][log_idx] = processed_log

def process_initialize_log(w3, log, pool_data, blocknum):
    # Get initialization data
    pool = pool_data["pool"]
    
    fee = pool.functions.fee().call(block_identifier=blocknum)
    tick_spacing = pool.functions.tickSpacing().call(block_identifier=blocknum)

    # Get trace for the current transaction
    trace = w3.tracing.trace_replay_transaction(log["transactionHash"])

    caller = None

    # Look for swap calls to the pool contract
    for traceitem in trace["trace"]:
        if traceitem["type"] == "call":
            if traceitem["action"]["to"] == pool_data["pool"].address:
                if traceitem["action"]["input"][0:4] == b"\xf6\x37\x73\x1d": # Initialize selector
                    caller = traceitem["action"]["from"]


    #print(log)

    return {
        "type": "initialize",
        "txn_hash": log["transactionHash"].hex(),
        "caller": caller,
        "data": {
            "deploy_data": {
                "token0": Web3.to_checksum_address(pool_data["token0"].address),
                "token1": Web3.to_checksum_address(pool_data["token1"].address),
                "fee": fee,
                "tick_spacing": tick_spacing
            },
            "initialize_data": {
                "sqrt_price_x96": log["args"]["sqrtPriceX96"],
            }
        }
    }

def process_mint_log(w3, log, pool_data, blocknum):
    return {
        "type": "mint", 
        "txn_hash": log["transactionHash"].hex(),
        "caller": Web3.to_checksum_address(log["args"]["sender"]),
        "data": {
            "recipient": Web3.to_checksum_address(log["args"]["owner"]),
            "tick_lower": log["args"]["tickLower"],
            "tick_upper": log["args"]["tickUpper"],
            "amount": log["args"]["amount"],
            "data": "not-implemented-yet"
        },
        "other": {
            "amount0": log["args"]["amount0"],
            "amount1": log["args"]["amount1"]
        }
    }

def process_burn_log(w3, log, pool_data, blocknum):
    return {
        "type": "burn",
        "txn_hash": log["transactionHash"].hex(),
        "caller": Web3.to_checksum_address(log["args"]["owner"]),
        "data": {
            "tick_lower": log["args"]["tickLower"],
            "tick_upper": log["args"]["tickUpper"],
            "amount": log["args"]["amount"],
        }
    }

def process_collect_log(w3, log, pool_data, blocknum):
    # Get trace for the current transaction
    trace = w3.tracing.trace_replay_transaction(log["transactionHash"])

    num_collects = 0
    collect_args = None

    # Look for swap calls to the pool contract
    for traceitem in trace["trace"]:
        if traceitem["action"]["to"] == pool_data["pool"].address:
            if traceitem["action"]["input"][0:4] == b"\x4f\x1e\xb3\xd8": # Collect selector
                collect_args = decode(
                    ["address", "int24", "int24", "uint128", "uint128"],
                    traceitem["action"]["input"][4:]
                )
                num_collects += 1

    if num_collects > 1:
        print("more than one to same pool in swap in transaction, need to be more specific")
        exit(0)

    return {
        "type": "collect",
        "txn_hash": log["transactionHash"].hex(),
        "caller": Web3.to_checksum_address(log["args"]["owner"]),
        "data": {
            "recipient": Web3.to_checksum_address(collect_args[0]),
            "tick_lower": collect_args[1],
            "tick_upper": collect_args[2],
            "amount_0_requested": collect_args[3],
            "amount_1_requested": collect_args[4]
        }
    }

def process_swap_log(w3, log, pool_data, blocknum):
    # Get trace for the current transaction
    trace = w3.tracing.trace_replay_transaction(log["transactionHash"])

    num_swaps = 0
    swap_args = None

    # Look for swap calls to the pool contract
    for traceitem in trace["trace"]:
        if traceitem["type"] != "suicide":
            if traceitem["action"]["to"] == pool_data["pool"].address:
                if traceitem["action"]["input"][0:4] == b"\x12\x8a\xcb\x08": # Swap selector
                    swap_args = decode(
                        ["address", "bool", "int256", "uint160", "bytes"],
                        traceitem["action"]["input"][4:]
                    )
                    num_swaps += 1

    if num_swaps > 1:
        print("more than one to same pool in swap in transaction, need to be more specific")
        exit(0)

    return {
        "type": "swap",
        "txn_hash": log["transactionHash"].hex(),
        "caller": Web3.to_checksum_address(log["args"]["sender"]),
        "data": {
            "recipient": Web3.to_checksum_address(swap_args[0]),
            "zero_for_one": swap_args[1],
            "amount_specified": swap_args[2],
            "sqrt_price_limit_x96": swap_args[3],
            "data": "0x" + swap_args[4].hex()
        },
        "other": {
            "amount0": log["args"]["amount0"],
            "amount1": log["args"]["amount1"]
        }
    }

def process_flash_log(w3, log, pool_data, blocknum):
    return {
        "type": "flash",
        "txn_hash": log["transactionHash"].hex(),
        "caller": Web3.to_checksum_address(log["args"]["sender"]),
        "data": {
            "recipient": Web3.to_checksum_address(log["args"]["recipient"]),
            "amount0": log["args"]["amount0"],
            "amount1": log["args"]["amount1"],
            "data": "to-be-implemented"
        },
        "repaid": {
            "amount0": log["args"]["repaid0"],
            "amount1": log["args"]["repaid1"]
        }
    }

def main():
    eth_rpc_url = os.getenv("ETH_RPC_URL")
    w3 = Web3(Web3.HTTPProvider(eth_rpc_url))

    latest_block = w3.eth.block_number
    blocknum = POOL_DEPLOYMENT_BLOCK

    pool_abi = load_abi("PoolUtils/out/UniswapV3Pool.sol/UniswapV3Pool.json")
    erc20_abi = load_abi("PoolUtils/out/MintableERC20.sol/MintableERC20.json")

    pool = w3.eth.contract(address=POOL_ADDRESS, abi=pool_abi)
    token0 = pool.functions.token0().call(block_identifier=blocknum)
    token0 = w3.eth.contract(address=token0, abi=erc20_abi)

    token1 = pool.functions.token1().call(block_identifier=blocknum)
    token1 = w3.eth.contract(address=token1, abi=erc20_abi)
    
    pool_data = {
        "pool": pool,
        "token0": token0,
        "token1": token1
    }

    all_interactions = []

    while blocknum < latest_block:
        block_interactions = get_pool_interactions(w3, pool_data, blocknum)
        print(blocknum)
        if len(block_interactions) != 0:
            all_interactions.append(block_interactions)
            print(json.dumps(block_interactions, indent=4))

            # Write all_interactions to a JSON file
            with open("interactions/interactions.json", "w") as file:
                json.dump(all_interactions, file, indent=4)
        
        blocknum += 1

if __name__ == "__main__":
    main()
