// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.7.0;

import "lib/v3-core/contracts/UniswapV3Factory.sol";
import "lib/v3-core/contracts/UniswapV3Pool.sol";

// Use inheritance to make foundry compile our desired import contracts
contract CompileTrick is UniswapV3Factory, UniswapV3Pool {}
