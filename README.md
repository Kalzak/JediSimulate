# JediSimulate

---

## How to run the Uniswap/Ethereum side

- Install some python dependencies (idk I'll figure out exactly the ones later)
- Install anvil (foundry link to go here)
- `cd` into the `Uniswap/PoolUtils` and run `forge install`, then `forge build` to built helper contracts
- Run `bash start_uniswap_anvil.sh` to start the node
- In another terminal run `python3 Test.py` to see how the proof of concept runs

