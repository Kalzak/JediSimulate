pragma solidity ^0.8.13;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "lib/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import "lib/v3-core/contracts/interfaces/callback/IUniswapV3MintCallback.sol";
import "lib/v3-core/contracts/interfaces/callback/IUniswapV3FlashCallback.sol";
import "lib/v3-core/contracts/interfaces/callback/IUniswapV3SwapCallback.sol";

contract UserContract is IUniswapV3MintCallback, IUniswapV3FlashCallback, IUniswapV3SwapCallback {
    IUniswapV3Pool public pool;
    IERC20 public token0;
    IERC20 public token1;

    constructor(IUniswapV3Pool _pool, IERC20 _token0, IERC20 _token1) {
        pool = _pool;
        token0 = _token0;
        token1 = _token1;
    }

    function mint(
        address recipient,
        int24 tickLower,
        int24 tickUpper,
        uint128 amount,
        bytes calldata data
    ) external  {
        pool.mint(recipient, tickLower, tickUpper, amount, data);
    }

    function burn(
        int24 tickLower,
        int24 tickUpper,
        uint128 amount
    ) external {
        pool.burn(tickLower, tickUpper, amount);
    }

    function flash(
        address recipient,
        uint256 amount0,
        uint256 amount1,
        bytes calldata data
    ) external  {
        pool.flash(recipient, amount0, amount1, data);
    }

    function swap(
        address recipient,
        bool zeroForOne,
        int256 amountSpecified,
        uint160 sqrtPriceLimitX96,
        bytes calldata data
    ) external  {
        pool.swap(recipient, zeroForOne, amountSpecified, sqrtPriceLimitX96, data);
    }

    function collect(
        address recipient,
        int24 tickLower,
        int24 tickUpper,
        uint128 amount0Requested,
        uint128 amount1Requested
    ) external {
        pool.collect(recipient, tickLower, tickUpper, amount0Requested, amount1Requested);
    }

    function uniswapV3FlashCallback(
        uint256 fee0,
        uint256 fee1,
        bytes calldata data
    ) external {
        // Just to get rid of compiler warnings
        fee0 = fee0;
        fee1 = fee1;
        data = data;
        (bool success, ) = address(0).call("");
        success = success;
    }

    function uniswapV3MintCallback(
        uint256 amount0Owed,
        uint256 amount1Owed,
        bytes calldata data
    ) external  {
        token0.transfer(address(pool), amount0Owed);
        token1.transfer(address(pool), amount1Owed);
        // Just to get rid of compiler warnings
        data = data;
    }

    function uniswapV3SwapCallback(
        int256 amount0Delta,
        int256 amount1Delta,
        bytes calldata data
    ) external  {
        if (amount0Delta > 0) {
            token0.transfer(address(pool), uint256(amount0Delta));
        } 
        if (amount1Delta > 0){
            token1.transfer(address(pool), uint256(amount1Delta));
        }
        // Just to get rid of compiler warnings
        data = data;
    }
}
