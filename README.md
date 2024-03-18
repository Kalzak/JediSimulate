# JediSimulate

---

## How to run the Uniswap/Ethereum side

- ```python3 -m venv simulation-env```
- ```source simulation-env/bin/activate```
- ```pip install --requirement pip_requirements.txt```
- Install anvil [link to installation](https://github.com/foundry-rs/foundry/tree/master/crates/anvil#installation)
- Install katana [link to installation](https://book.starknet.io/ch02-05-katana.html#getting-started-with-katana)
- `cd` into the `Uniswap/PoolUtils` and run `forge install`, then `forge build` to built helper contracts
- `cd` into the `Jediswap/PoolUtils` and run `scarb build`
- Run `bash start_uniswap_anvil.sh` to start the Ethereum node
- In another terminal run `bash start_jediswap_katana.sh` to start Starknet node
- In separate terminal run `bash run_simulation.sh` to see how the proof of concept runs

