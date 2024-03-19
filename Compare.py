from Uniswap import UniswapPool
from Jediswap import JediswapPool
import json

def main():
    # Open the interactions file to get data
    with open("interactions.json", "r") as file:
        all_interactions = json.load(file)

    # Initialize both pools
    init_interaction = all_interactions[0].pop(0)
    pool = UniswapPool(init_interaction)
    jedi_pool = JediswapPool(init_interaction)
    
    # Tracks all unique positions, used for comparisons
    positions = {}

    for block_interactions in all_interactions:
        for interaction in block_interactions:
            
            # Execute the interaction
            if interaction["type"] == "mint":
                execute_mint(pool, jedi_pool, interaction, positions)
            elif interaction["type"] == "burn":
                execute_burn(pool, jedi_pool, interaction)
            elif interaction["type"] == "swap":
                execute_swap(pool, jedi_pool, interaction)
            elif interaction["type"] == "collect":
                execute_collect(pool, jedi_pool, interaction)
            elif interaction["type"] == "flash":
                print("flashloan encountered")
                exit(0)    
            else:
                print("unknown interaction")
                exit(0)

            # All positions should be same for both pools 
            compare_all_positions(positions, pool, jedi_pool)

def execute_mint(uni_pool, jedi_pool, interaction, positions):
    # Extract out the unique fields that will represent the position
    position = {
        "owner": interaction["data"]["recipient"],
        "tick_lower": interaction["data"]["tick_lower"],
        "tick_upper": interaction["data"]["tick_upper"]
    }

    # Execute the mint on both pools
    uni_status, uni_reason = uni_pool.mint(interaction)
    jedi_status, jedi_reason, jedi_txhash_obj, old_position = jedi_pool.mint(interaction)
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
def compare_all_positions(positions, uni_pool, jedi_pool):
    for position_dict_key in positions.keys():
        position_key = positions[position_dict_key]

        uni_position_data = uni_pool.get_position(
            position_key["owner"], position_key["tick_lower"], position_key["tick_upper"]
        )
        jedi_position_data = jedi_pool.get_position(
            position_key["owner"], position_key["tick_lower"], position_key["tick_upper"]
        )

        # Once the jediswap side works, we can actually let the script execute enough to compare positions
        # Until then not much can be done


if __name__ == "__main__":
    main()