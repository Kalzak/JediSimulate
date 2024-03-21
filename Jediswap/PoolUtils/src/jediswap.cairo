// @title JediSwap V2 Swap Router
// @notice Router for stateless execution of swaps against JediSwap V2

use starknet::ContractAddress;
// use yas_core::numbers::signed_integer::{i32::i32, i128::i128, i256::i256};
use yas_core::numbers::signed_integer::{
    i8::i8, i16::i16, i32::i32, i64::i64, i128::i128, i256::i256
};
// use jediswap_v2_core::jediswap_v2_pool::JediSwapV2Pool;
// use jediswap;


#[starknet::interface]
trait IJediSwapFuzz<TContractState> {
    // Addition
    fn add_i8(self: @TContractState, number1: i8, number2: i8) -> i8;
    fn add_i16(self: @TContractState, number1: i16, number2: i16) -> i16;
    fn add_i32(self: @TContractState, number1: i32, number2: i32) -> i32;
    fn add_i64(self: @TContractState, number1: i64, number2: i64) -> i64;
    fn add_i128(self: @TContractState, number1: i128, number2: i128) -> i128;
    fn add_i256(self: @TContractState, number1: i256, number2: i256) -> i256;
    // Multiplication
    fn mul_i8(self: @TContractState, number1: i8, number2: i8) -> i8;
    fn mul_i16(self: @TContractState, number1: i16, number2: i16) -> i16;
    fn mul_i32(self: @TContractState, number1: i32, number2: i32) -> i32;
    fn mul_i64(self: @TContractState, number1: i64, number2: i64) -> i64;
    fn mul_i128(self: @TContractState, number1: i128, number2: i128) -> i128;
    fn mul_i256(self: @TContractState, number1: i256, number2: i256) -> i256;
    // Subtraction
    fn sub_i8(self: @TContractState, number1: i8, number2: i8) -> i8;
    fn sub_i16(self: @TContractState, number1: i16, number2: i16) -> i16;
    fn sub_i32(self: @TContractState, number1: i32, number2: i32) -> i32;
    fn sub_i64(self: @TContractState, number1: i64, number2: i64) -> i64;
    fn sub_i128(self: @TContractState, number1: i128, number2: i128) -> i128;
    fn sub_i256(self: @TContractState, number1: i256, number2: i256) -> i256;
    // Division
    fn div_i8(self: @TContractState, number1: i8, number2: i8) -> i8;
    fn div_i16(self: @TContractState, number1: i16, number2: i16) -> i16;
    fn div_i32(self: @TContractState, number1: i32, number2: i32) -> i32;
    fn div_i64(self: @TContractState, number1: i64, number2: i64) -> i64;
    fn div_i128(self: @TContractState, number1: i128, number2: i128) -> i128;
    fn div_i256(self: @TContractState, number1: i256, number2: i256) -> i256;
}

#[starknet::contract]
mod JediSwapFuzz {
    // use super::{
    //     ExactInputSingleParams, ExactInputParams, ExactOutputSingleParams, ExactOutputParams,
    //     PathData, SwapCallbackData
    // };
    // use openzeppelin::token::erc20::interface::{
    //     IERC20Dispatcher, IERC20DispatcherTrait, IERC20CamelDispatcher, IERC20CamelDispatcherTrait
    // };
    use starknet::{
        ContractAddress, get_contract_address, get_caller_address, get_block_timestamp,
        contract_address_to_felt252
    };
    use integer::{u256_from_felt252, BoundedInt};

    // use jediswap_v2_core::libraries::tick_math::TickMath::{
    //     get_sqrt_ratio_at_tick, MIN_TICK, MAX_TICK
    // };

    // use jediswap_v2_core::jediswap_v2_pool::{
    //     IJediSwapV2PoolDispatcher, IJediSwapV2PoolDispatcherTrait
    // };
    // use jediswap_v2_core::jediswap_v2_factory::{
    //     IJediSwapV2FactoryDispatcher, IJediSwapV2FactoryDispatcherTrait
    // };

    // use yas_core::numbers::signed_integer::{
    //     i32::i32, i64::i64, i128::{i128, u128Intoi128}, i256::{i256, i256TryIntou256},
    //     integer_trait::IntegerTrait
    // };
    use yas_core::utils::math_utils::FullMath::mul_div;

    use yas_core::utils::math_utils::BitShift::BitShiftTrait;

    use yas_core::numbers::signed_integer::{
        i8::i8, i16::i16, i32::i32, i64::i64, i128::i128, i256::i256,
        integer_trait::IntegerTrait
    };

    // use jediswap_v2_core::jediswap_v2_pool;



    #[storage]
    struct Storage {
    }

    #[constructor]
    fn constructor(ref self: ContractState) {}

    #[external(v0)]
    impl JediSwapFuzz of super::IJediSwapFuzz<ContractState> {
       // Addition
        fn add_i8(self: @ContractState, number1: i8, number2: i8) -> i8 {
            number1 + number2
        }
        fn add_i16(self: @ContractState, number1: i16, number2: i16) -> i16 {
            number1 + number2
        }
        fn add_i32(self: @ContractState, number1: i32, number2: i32) -> i32 {
            number1 + number2
        }
        fn add_i64(self: @ContractState, number1: i64, number2: i64) -> i64 {
            number1 + number2
        }
        fn add_i128(self: @ContractState, number1: i128, number2: i128) -> i128 {
            number1 + number2
        }
        fn add_i256(self: @ContractState, number1: i256, number2: i256) -> i256 {
            number1 + number2
        }
        // Multiplication
        fn mul_i8(self: @ContractState, number1: i8, number2: i8) -> i8 {
            number1 * number2
        }
        fn mul_i16(self: @ContractState, number1: i16, number2: i16) -> i16 {
            number1 * number2
        }
        fn mul_i32(self: @ContractState, number1: i32, number2: i32) -> i32 {
            number1 * number2
        }
        fn mul_i64(self: @ContractState, number1: i64, number2: i64) -> i64 {
            number1 * number2
        }
        fn mul_i128(self: @ContractState, number1: i128, number2: i128) -> i128 {
            number1 * number2
        }
        fn mul_i256(self: @ContractState, number1: i256, number2: i256) -> i256 {
            number1 * number2
        }
        // Subtraction
        fn sub_i8(self: @ContractState, number1: i8, number2: i8) -> i8 {
            number1 - number2
        }
        fn sub_i16(self: @ContractState, number1: i16, number2: i16) -> i16 {
            number1 - number2
        }
        fn sub_i32(self: @ContractState, number1: i32, number2: i32) -> i32 {
            number1 - number2
        }
        fn sub_i64(self: @ContractState, number1: i64, number2: i64) -> i64 {
            number1 - number2
        }
        fn sub_i128(self: @ContractState, number1: i128, number2: i128) -> i128 {
            number1 - number2
        }
        fn sub_i256(self: @ContractState, number1: i256, number2: i256) -> i256 {
            number1 - number2
        }
        // Division
        fn div_i8(self: @ContractState, number1: i8, number2: i8) -> i8 {
            number1 / number2
        }
        fn div_i16(self: @ContractState, number1: i16, number2: i16) -> i16 {
            number1 / number2
        }
        fn div_i32(self: @ContractState, number1: i32, number2: i32) -> i32 {
            number1 / number2
        }
        fn div_i64(self: @ContractState, number1: i64, number2: i64) -> i64 {
            number1 / number2
        }
        fn div_i128(self: @ContractState, number1: i128, number2: i128) -> i128 {
            number1 / number2
        }
        fn div_i256(self: @ContractState, number1: i256, number2: i256) -> i256 {
            number1 / number2
        }
    }

    #[generate_trait]
    impl InternalImpl of InternalTrait {}
        
}
