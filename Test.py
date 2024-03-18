from Uniswap import UniswapPool
import json

with open("interactions.json", "r") as file:
    all_interactions = json.load(file)

init_interaction = all_interactions[0].pop(0)

pool = UniswapPool(init_interaction)

for block_interactions in all_interactions:
    for interaction in block_interactions:
        
        status = None
        reason = None

        if interaction["type"] == "mint":
            status, reason = pool.mint(interaction)
        elif interaction["type"] == "burn":
            status, reason = pool.burn(interaction)
        elif interaction["type"] == "swap":
            status, reason = pool.swap(interaction)
        elif interaction["type"] == "collect":
            status, reason = pool.collect(interaction)
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
