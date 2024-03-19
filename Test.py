from Uniswap import UniswapPool
from Jediswap import JediswapPool
import json

with open("interactions.json", "r") as file:
    all_interactions = json.load(file)

init_interaction = all_interactions[0].pop(0)

pool = UniswapPool(init_interaction)
jedi_pool = JediswapPool(init_interaction)
positions = []

for block_interactions in all_interactions:
    for interaction in block_interactions:
        
        status = None
        reason = None

        if interaction["type"] == "mint":
            status, reason = pool.mint(interaction)
            status, reason, tx_hash_obj, position = jedi_pool.mint(interaction)
            positions.append(position)
        elif interaction["type"] == "burn":
            status, reason = pool.burn(interaction)
            status, reason, tx_hash_obj = jedi_pool.burn(interaction)
        elif interaction["type"] == "swap":
            status, reason = pool.swap(interaction)
            status, reason, tx_hash_obj = jedi_pool.swap(interaction)
        elif interaction["type"] == "collect":
            status, reason = pool.collect(interaction)
            status, reason, tx_hash_obj = jedi_pool.collect(interaction)
        elif interaction["type"] == "flash":
            print("flashloan encountered")
            exit(0)    
        else:
            print("unknown interaction")
            exit(0)

        if status == "reverted":
            print("reverted interaction")
            print(reason)
            exit(0)
        
        ######### COMPARE POSITIONS OF UNISWAP AND JEDISWAP ########
        for p in positions:
            p_info_jedi = jedi_pool.get_position(
                p["owner"], p["tick_lower"], p["tick_upper"]
            )
            # print(p_info_jedi)
            pool.get_position(
                p["owner"], p["tick_lower"], p["tick_upper"]
            )
