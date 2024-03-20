from alive_progress import alive_bar
import json
import sys

from Uniswap import UniswapPool
from Jediswap import JediswapPool

def main(interactions_file_path):
    # Open the interactions file to get data
    with open(interactions_file_path, "r") as file:
        all_interactions = json.load(file)

    # Initialize both pools
    init_interaction = all_interactions[0].pop(0)
    pool = UniswapPool(init_interaction)
    jedi_pool = JediswapPool(init_interaction)
    
    # Tracks all unique positions, used for comparisons
    positions = {}
    counter = 0
    interval = 100

    with alive_bar(len(all_interactions)) as bar:
        for block_interactions in all_interactions:
            for interaction in block_interactions:
                
                # Set data arguments to zero because not used currently
                if "data" in interaction["data"].keys():
                    interaction["data"]["data"] = "N/A"
                print(json.dumps(interaction, indent=4))

                # Prepare the token sender and recipient fields
                sender_address = None
                recipient_address = None

                # Execute the interactionnteractions.json

                if interaction["type"] == "mint":
                    execute_mint(pool, jedi_pool, interaction, positions)
                    sender_address = interaction["caller"]
                    recipient_address = interaction["data"]["recipient"]

                elif interaction["type"] == "burn":
                    execute_burn(pool, jedi_pool, interaction)
                    recipient_address = interaction["caller"]

                elif interaction["type"] == "swap":
                    execute_swap(pool, jedi_pool, interaction)
                    sender_address = interaction["caller"]
                    recipient_address = interaction["data"]["recipient"]

                elif interaction["type"] == "collect":
                    execute_collect(pool, jedi_pool, interaction)
                    recipient_address = interaction["data"]["recipient"]

                elif interaction["type"] == "flash":
                    print("flashloan encountered")
                    exit(0)    
                
                else:
                    print("unknown interaction")
                    exit(0)

                if counter % interval == 0:
                    print("======== COMPARISON CHECKS ======== ")
                    # All positions should be same for both pools 
                    compare_pool_data_and_positions(positions, pool, jedi_pool)
                    print("============ CHECKS OK ============ ")

                
                # Verify token balances
                if sender_address:
                    verify_balances(sender_address, pool, jedi_pool)
                if recipient_address and sender_address != recipient_address:
                    verify_balances(recipient_address, pool, jedi_pool)    
                
            counter += 1

            bar()

def verify_balances(address, uni_pool, jedi_pool):
    uni_token0 = uni_pool.get_token0()
    jedi_token0 = jedi_pool.get_token0()
    uni_token1 = uni_pool.get_token1()
    jedi_token1 = jedi_pool.get_token1()

    uni_token0_balance = uni_pool.get_token_balance(uni_token0, address)
    jedi_token0_balance = jedi_pool.get_token_balance(jedi_token0, address)
    uni_token1_balance = uni_pool.get_token_balance(uni_token1, address)
    jedi_token1_balance = jedi_pool.get_token_balance(jedi_token1, address)
    
    if uni_token0_balance != jedi_token0_balance:
        print("########################### INCORRECT BALANCE ###########################")
        print("UNI BALANCE: ", uni_token0_balance)
        print("JEDI BALANCE: ", jedi_token0_balance)
        exit()

    if uni_token1_balance != jedi_token1_balance:
        print("########################### INCORRECT BALANCE ###########################")
        print("UNI BALANCE: ", uni_token1_balance)
        print("JEDI BALANCE: ", jedi_token1_balance)
        exit()

def execute_mint(uni_pool, jedi_pool, interaction, positions):
    # Extract out the unique fields that will represent the position
    position = {
        "owner": interaction["data"]["recipient"],
        "tick_lower": interaction["data"]["tick_lower"],
        "tick_upper": interaction["data"]["tick_upper"]
    }

    # Execute the mint on both pools
    uni_status, uni_reason = uni_pool.mint(interaction)
    jedi_status, jedi_reason, jedi_txhash_obj = jedi_pool.mint(interaction)
    check_execution_status(uni_status, jedi_status, uni_reason, jedi_reason, jedi_txhash_obj)

    # Add the position to positions set (if unique)
    add_to_positions(positions, position)

def execute_burn(uni_pool, jedi_pool, interaction):
    uni_status, uni_reason = uni_pool.burn(interaction)
    jedi_status, jedi_reason, jedi_txhash_obj = jedi_pool.burn(interaction)
    check_execution_status(uni_status, jedi_status, uni_reason, jedi_reason, jedi_txhash_obj)

def execute_swap(uni_pool, jedi_pool, interaction):
    uni_status, uni_reason = uni_pool.swap(interaction)
    jedi_status, jedi_reason, jedi_txhash_obj = jedi_pool.swap(interaction)
    check_execution_status(uni_status, jedi_status, uni_reason, jedi_reason, jedi_txhash_obj)

def execute_collect(uni_pool, jedi_pool, interaction):
    uni_status, uni_reason = uni_pool.collect(interaction)
    jedi_status, jedi_reason, jedi_txhash_obj = jedi_pool.collect(interaction)
    check_execution_status(uni_status, jedi_status, uni_reason, jedi_reason, jedi_txhash_obj)

def check_execution_status(uni_status, jedi_status, uni_reason, jedi_reason, jedi_txhash_obj):
    # Ensure both pools have same status
    if uni_status != jedi_status:
        print("Uni revert:", uni_reason)
        print("Jedi revert:", jedi_reason)
        print("Jedi txhashobj:", jedi_txhash_obj)
        exit(0)

# Only adds a position to the array if it's unique
def add_to_positions(positions, position):
    hashed_position = hash(json.dumps(position))
    if hashed_position not in positions.keys():
        positions[hashed_position] = position

# Checks for each position that they are equal across both pools
def compare_pool_data_and_positions(positions, uni_pool, jedi_pool):
    passed = True
    uni_sqrt_price = uni_pool.get_sqrt_price_X96()
    jedi_sqrt_price = jedi_pool.get_sqrt_price_X96()
    if jedi_sqrt_price != uni_sqrt_price:
        passed = False
        print("INCORRECT SQRT PRICE")
        print("UNISWAP SQRT PRICE:", uni_sqrt_price)
        print("JEDISWAP SQRT PRICE:", jedi_sqrt_price)

    uni_tick = uni_pool.get_tick()
    jedi_tick = jedi_pool.get_tick()
    if uni_tick != jedi_tick:
        passed = False
        print("INCORRECT TICK")
        print("UNISWAP TICK:", uni_tick)
        print("JEDISWAP TICK:", jedi_tick)

    uni_fee0 = uni_pool.get_fee_growth_global_0_X128()
    jedi_fee0 = jedi_pool.get_fee_growth_global_0_X128()
    if uni_fee0 != jedi_fee0:
        passed = False
        print("INCORRECT FEE GROWTH 0")
        print("UNISWAP FEE GROWTH 0:", uni_fee0)
        print("JEDISWAP FEE GROWTH 0:", jedi_fee0)

    uni_fee1 = uni_pool.get_fee_growth_global_1_X128()
    jedi_fee1 = jedi_pool.get_fee_growth_global_1_X128()
    if uni_fee1 != jedi_fee1:
        passed = False
        print("INCORRECT FEE GROWTH 1")
        print("UNISWAP FEE GROWTH 1:", uni_fee1)
        print("JEDISWAP FEE GROWTH 1:", jedi_fee1)

    uni_liquidity = uni_pool.get_liquidity()
    jedi_liquidity = jedi_pool.get_liquidity()
    if uni_liquidity != jedi_liquidity:
        passed = False
        print("INCORRECT LIQUIDITY")
        print("UNISWAP LIQUIDITY:", uni_liquidity)
        print("JEDISWAP LIQUIDITY:", jedi_liquidity)
    
    # Positions check
    for position_dict_key in positions.keys():
        position_key = positions[position_dict_key]

        uni_position_data = uni_pool.get_position(
            position_key["owner"], position_key["tick_lower"], position_key["tick_upper"]
        )
        jedi_position_data = jedi_pool.get_position(
            position_key["owner"], position_key["tick_lower"], position_key["tick_upper"]
        )

        if uni_position_data != jedi_position_data:
            passed = False
            print("########################### INCORRECT POSITION ###########################")
            print("UNI POSITION: ", uni_position_data)
            print("JEDI POSITION: ", jedi_position_data)
    
    if not passed:
        exit()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 Compare.py <interactions_file_path>")
        exit(0)
    main(sys.argv[1])