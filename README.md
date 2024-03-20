# JediSimulate

This tool compares the Uniswap protocol on EVM against the Jediswap protocol on Starknet. It creates two separate local nodes (Anvil and Katana) with each protocol implementation, and a sequence of interactions are passed to both. After each interaction, observable fields such as position data and token balances are verified to be the same across both nodes. 

Built by Nethermind as part of a security and code-review engagement with the Jediswap team. 

## Dependencies and setup

1. Clone the repository to your local machine
1. Create and active a virtual environment: `python3 -m vern simulation-env`
1. Install python dependencies: `pip install --requirements pip_requirements.txt`
1. Install Foundry, [link to installation](https://github.com/foundry-rs/)
1. Install Katana, [link to installation](https://book.starknet.io/ch02-05-katana.html#getting-started-with-katana) (version `katana 0.6.0-alpha.6`)
1. Install Starkli, [link to installation](https://github.com/xJonathanLEI/starkli)
1. Install Scarb via `asdf`, [link to installation](https://docs.swmansion.com/scarb/download.html#install-via-asdf), set version to `2.4.3` with `asdf local scarb 2.4.3`
1. Enter dir `Uniswap/PoolUtils` and run `forge build` to compile Uniswap and helper contracts
1. Enter dir `Jediswap/PoolUtils` and run `scarb build` to compile Jediswap and helper contracts

## How to run

All of the following interactions should be executed in a different terminal.

1. `bash start_uniswap_anvil.sh`
1. `bash start_jediswap_katana.sh`
1. `bash run_simulation.sh`