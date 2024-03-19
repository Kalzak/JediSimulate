// @title JediSwap V2 Swap Router
// @notice Router for stateless execution of swaps against JediSwap V2

use starknet::ContractAddress;
use yas_core::numbers::signed_integer::{i32::i32, i128::i128, i256::i256};
// use jediswap_v2_core::jediswap_v2_pool::JediSwapV2Pool;
// use jediswap;


#[starknet::interface]
trait IJediSwapV2Account<TContractState> {
    fn get_pool(self: @TContractState) -> ContractAddress;
    fn transfer_token(
            self: @TContractState, 
            token_addr: ContractAddress,
            recipient: ContractAddress,
            amount: u128
    );
    fn initialize(ref self: TContractState, sqrt_price_X96: u256);
    fn mint(
        ref self: TContractState,
        recipient: ContractAddress,
        tick_lower: i32,
        tick_upper: i32,
        amount: u128,
        data: Array<felt252>
    ) -> (u256, u256);
    fn collect(
        ref self: TContractState,
        recipient: ContractAddress,
        tick_lower: i32,
        tick_upper: i32,
        amount0_requested: u128,
        amount1_requested: u128
    ) -> (u128, u128);
    fn burn(
        ref self: TContractState, tick_lower: i32, tick_upper: i32, amount: u128
    ) -> (u256, u256);
    fn swap(
        ref self: TContractState,
        recipient: ContractAddress,
        zero_for_one: u8,
        amount_specified: i256,
        sqrt_price_limit_X96: u256,
        data: Array<felt252>
    ) -> (i256, i256);
    fn jediswap_v2_swap_callback(
        ref self: TContractState,
        amount0_delta: i256,
        amount1_delta: i256,
        callback_data_span: Span<felt252>
    );
    fn jediswap_v2_mint_callback(
        ref self: TContractState,
        amount0_owed: u256,
        amount1_owed: u256,
        callback_data_span: Span<felt252>
    );
}

#[starknet::contract]
mod JediSwapV2Account {
    // use super::{
    //     ExactInputSingleParams, ExactInputParams, ExactOutputSingleParams, ExactOutputParams,
    //     PathData, SwapCallbackData
    // };
    use openzeppelin::token::erc20::interface::{
        IERC20Dispatcher, IERC20DispatcherTrait, IERC20CamelDispatcher, IERC20CamelDispatcherTrait
    };
    use starknet::{
        ContractAddress, get_contract_address, get_caller_address, get_block_timestamp,
        contract_address_to_felt252
    };
    use integer::{u256_from_felt252, BoundedInt};

    use jediswap_v2_core::libraries::tick_math::TickMath::{
        get_sqrt_ratio_at_tick, MIN_TICK, MAX_TICK
    };

    use jediswap_v2_core::jediswap_v2_pool::{
        IJediSwapV2PoolDispatcher, IJediSwapV2PoolDispatcherTrait
    };
    use jediswap_v2_core::jediswap_v2_factory::{
        IJediSwapV2FactoryDispatcher, IJediSwapV2FactoryDispatcherTrait
    };

    use yas_core::numbers::signed_integer::{
        i32::i32, i64::i64, i128::{i128, u128Intoi128}, i256::{i256, i256TryIntou256},
        integer_trait::IntegerTrait
    };
    use yas_core::utils::math_utils::FullMath::mul_div;
    use yas_core::utils::math_utils::BitShift::BitShiftTrait;

    // use jediswap_v2_core::jediswap_v2_pool;



    #[storage]
    struct Storage {
        pool: ContractAddress,
        token0: ContractAddress,
        token1: ContractAddress,
        num: u8
    }

    #[constructor]
    fn constructor(ref self: ContractState, 
        pool: ContractAddress,
        token0: ContractAddress,
        token1: ContractAddress
    ) {
        self.pool.write(pool);
        self.token0.write(token0);
        self.token1.write(token1);
    }

    #[external(v0)]
    impl JediSwapV2Account of super::IJediSwapV2Account<ContractState> {
        fn get_pool(self: @ContractState) -> ContractAddress {
            self.pool.read()
        }

        fn transfer_token(
            self: @ContractState, 
            token_addr: ContractAddress,
            recipient: ContractAddress,
            amount: u128
        ) {
            let token_dispatcher = IERC20Dispatcher { contract_address: token_addr };
            token_dispatcher.transfer(recipient, amount.into());
        }

        fn initialize(ref self: ContractState, sqrt_price_X96: u256) {
            let pool_dispatcher = IJediSwapV2PoolDispatcher {
                contract_address: self.pool.read()
            };
            pool_dispatcher.initialize(
                sqrt_price_X96
            );
        }
        fn mint(
            ref self: ContractState,
            recipient: ContractAddress,
            tick_lower: i32,
            tick_upper: i32,
            amount: u128,
            data: Array<felt252>
        ) -> (u256, u256) {
            let pool_dispatcher = IJediSwapV2PoolDispatcher {
                contract_address: self.pool.read()
            };
            let mut data_temp: Array<felt252> = ArrayTrait::new();
            pool_dispatcher.mint(
                recipient,
                tick_lower,
                tick_upper,
                amount,
                data_temp
            )
        }
        fn collect(
            ref self: ContractState,
            recipient: ContractAddress,
            tick_lower: i32,
            tick_upper: i32,
            amount0_requested: u128,
            amount1_requested: u128
        ) -> (u128, u128) {
            let pool_dispatcher = IJediSwapV2PoolDispatcher {
                contract_address: self.pool.read()
            };
            pool_dispatcher.collect(
                recipient,
                tick_lower,
                tick_upper,
                amount0_requested,
                amount1_requested
            )
        }
        fn burn(
            ref self: ContractState, tick_lower: i32, tick_upper: i32, amount: u128
        ) -> (u256, u256) {
            let pool_dispatcher = IJediSwapV2PoolDispatcher {
                contract_address: self.pool.read()
            };
            pool_dispatcher.burn(
                tick_lower,
                tick_upper,
                amount
            )
        }

        fn swap(
            ref self: ContractState,
            recipient: ContractAddress,
            zero_for_one: u8,
            amount_specified: i256,
            sqrt_price_limit_X96: u256,
            data: Array<felt252>
        ) -> (i256, i256) {
            let pool_dispatcher = IJediSwapV2PoolDispatcher {
                contract_address: self.pool.read()
            };
            let zero_for_one_for_pool = if (zero_for_one == 0) {
                false
            } else {
                true
            };
            pool_dispatcher.swap(recipient, zero_for_one_for_pool, amount_specified, sqrt_price_limit_X96, data)
        }

        fn jediswap_v2_swap_callback(
            ref self: ContractState,
            amount0_delta: i256,
            amount1_delta: i256,
            mut callback_data_span: Span<felt252>
        ) {
            if (amount0_delta > IntegerTrait::<i256>::new(0, false)) {
                let token0_dispatcher = IERC20Dispatcher {
                    contract_address: self.token0.read()
                };
                token0_dispatcher.transfer(self.pool.read(), amount0_delta.mag);
            }
            if (amount1_delta > IntegerTrait::<i256>::new(0, false)) {
                let token1_dispatcher = IERC20Dispatcher {
                    contract_address: self.token1.read()
                };
                token1_dispatcher.transfer(self.pool.read(), amount1_delta.mag);
            }
        }

        fn jediswap_v2_mint_callback(
            ref self: ContractState,
            amount0_owed: u256,
            amount1_owed: u256,
            callback_data_span: Span<felt252>
        ) {
            let token0_dispatcher = IERC20Dispatcher {
                contract_address: self.token0.read()
            };
            token0_dispatcher.transfer(self.pool.read(), amount0_owed);

            let token1_dispatcher = IERC20Dispatcher {
                contract_address: self.token1.read()
            };
            token1_dispatcher.transfer(self.pool.read(), amount1_owed);
        }
    }

    #[generate_trait]
    impl InternalImpl of InternalTrait {}
        
}
