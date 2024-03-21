# JediSimulate

This tool compares the Uniswap protocol on EVM against the Jediswap protocol on Starknet. It creates two separate local nodes (Anvil and Katana) with each protocol implementation, and a sequence of interactions are passed to both. After each interaction, observable fields such as position data and token balances are verified to be the same across both nodes. 

Built by Nethermind as part of a security and code-review engagement with the Jediswap team. 

## Dependencies and setup

1. Clone the repository to your local machine
1. Create and active a virtual environment: `python3 -m venv simulation-env`
1. Activate the new environment: `source simulation-env/bin/activate`
1. Copy `.env_example` to a new file `.env`, you can add your RPC url if you want to collect interactions
1. Install python dependencies: `pip install --requirement pip_requirements.txt`
1. Install Foundry, [link to installation](https://github.com/foundry-rs/)
1. Install Katana, [link to installation](https://book.starknet.io/ch02-05-katana.html#getting-started-with-katana) (version `katana 0.6.0-alpha.6`)
1. Install Starkli, [link to installation](https://github.com/xJonathanLEI/starkli) (try version `0.1.20`)
1. Install Scarb via `asdf`, [link to installation](https://docs.swmansion.com/scarb/download.html#install-via-asdf), set version to `2.4.3` with `asdf local scarb 2.4.3`
1. Enter dir `Uniswap/PoolUtils` and run `forge build` to compile Uniswap and helper contracts
1. Enter dir `Jediswap/PoolUtils` and run `scarb build` to compile Jediswap and helper contracts

## Collecting interactions

The interactions tested on both protocols are extracted directly from Uniswap pools, meaning that all simulations done through this program are done from real on-chain data. It can take a long amount of time to collect this data, access to a personal node or high-throughput RPC url is recommended. The given RPC endpoint must support the `trace_replayTransaction` method.

1. Open `Interactions.py` and edit `POOL_ADDRESS` to your Uniswap pool of choice
1. Open `Interactions.py` and edit `POOL_DEPLOYMENT_BLOCK` to the block which the pool was deployed
1. Source `.env` to get your RPC url: `source .env`
1. Collect interactions: `python3 Interactions.py`
1. Allow this script to run as long as you like, ctrl+c to halt script
1. Output is placed in `interactions/interactions.json`
1. Consider renaming output to another name like `usdc-eth-interactions.json`

## How to run

All of the following interactions should be executed in a different terminal.

1. `bash start_uniswap_anvil.sh`
1. `bash start_jediswap_katana.sh`
1. `source .env; python3 Compare.py <interaction_file_path>`