from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.commitment_config import CommitmentLevel
from solders.pubkey import Pubkey
from spl.token.instructions import get_associated_token_address, create_associated_token_account
from scanner import TokenInfo
from raydium_dex import RaydiumDEX, PoolInfo
import time

class TokenBuyer:
    def __init__(self, rpc_client: Client, wallet: Keypair):
        self.rpc_client = rpc_client
        self.wallet = wallet
        self.max_slippage = 0.02  # 2% maximum slippage
        self.SOL_MINT = Pubkey.from_string("So11111111111111111111111111111111111111112")

    def buy_token(self, token: TokenInfo, amount_in_sol: float) -> bool:
        """
        Executes a purchase of the specified token using Raydium DEX.
        """
        try:
            print(f"Attempting to buy {token.symbol} with {amount_in_sol} SOL...")
            
            # 1. Get pool information
            pool_info = RaydiumDEX.get_pool_info(
                self.rpc_client,
                Pubkey(token.address)
            )
            
            if not pool_info:
                print("Could not find liquidity pool")
                return False
            
            # 2. Calculate amounts
            amount_in_lamports = int(amount_in_sol * 1e9)  # Convert SOL to lamports
            
            # Calculate expected output and price impact
            amount_out, price_impact = RaydiumDEX.calculate_swap_amounts(
                amount_in_lamports,
                pool_info.quote_reserve,  # SOL reserve
                pool_info.base_reserve    # Token reserve
            )
            
            # Check price impact
            if price_impact > self.max_slippage:
                print(f"Price impact too high: {price_impact:.2%}")
                return False
            
            # Calculate minimum amount out with slippage
            min_amount_out = int(amount_out * (1 - self.max_slippage))
            
            # 3. Get or create token account
            user_token_account = get_associated_token_address(
                self.wallet.public_key,
                Pubkey(token.address)
            )
            
            # Check if token account exists, if not create it
            account_info = self.rpc_client.get_account_info(str(user_token_account))
            if not account_info["result"]["value"]:
                print("Creating associated token account...")
                create_ix = create_associated_token_account(
                    self.wallet.public_key,
                    self.wallet.public_key,
                    Pubkey(token.address)
                )
                tx = Transaction().add(create_ix)
                self._send_and_confirm_transaction(tx)
                time.sleep(1)  # Wait for account creation
            
            # 4. Create swap instruction
            swap_ix = RaydiumDEX.create_swap_instruction(
                pool_info,
                self.wallet.public_key,
                self.wallet.public_key,  # SOL from wallet
                user_token_account,      # Token to ATA
                amount_in_lamports,
                min_amount_out,
                is_sol_to_token=True
            )
            
            # 5. Create and send transaction
            tx = Transaction().add(swap_ix)
            
            result = self._send_and_confirm_transaction(tx)
            if result:
                print(f"Successfully bought {token.symbol}")
                print(f"Expected output: {amount_out / 10**pool_info.base_decimals:.6f} {token.symbol}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error buying token: {str(e)}")
            return False

    def sell_token(self, token: TokenInfo, amount_tokens: float = None) -> bool:
        """
        Sells tokens. If amount_tokens is None, sells entire balance.
        """
        try:
            print(f"Attempting to sell {token.symbol}...")
            
            # 1. Get pool information
            pool_info = RaydiumDEX.get_pool_info(
                self.rpc_client,
                Pubkey(token.address)
            )
            
            if not pool_info:
                print("Could not find liquidity pool")
                return False
            
            # 2. Get token account
            user_token_account = get_associated_token_address(
                self.wallet.public_key,
                Pubkey(token.address)
            )
            
            # 3. Get token balance if selling entire position
            if amount_tokens is None:
                balance = self._get_token_balance(token.address)
                if balance == 0:
                    print("No tokens to sell")
                    return False
                amount_tokens = balance
            else:
                amount_tokens = int(amount_tokens * 10**pool_info.base_decimals)
            
            # 4. Calculate expected output and price impact
            amount_out, price_impact = RaydiumDEX.calculate_swap_amounts(
                amount_tokens,
                pool_info.base_reserve,    # Token reserve
                pool_info.quote_reserve,   # SOL reserve
                is_sol_to_token=False
            )
            
            # Check price impact
            if price_impact > self.max_slippage:
                print(f"Price impact too high: {price_impact:.2%}")
                return False
            
            # Calculate minimum amount out with slippage
            min_amount_out = int(amount_out * (1 - self.max_slippage))
            
            # 5. Create swap instruction
            swap_ix = RaydiumDEX.create_swap_instruction(
                pool_info,
                self.wallet.public_key,
                user_token_account,      # Token from ATA
                self.wallet.public_key,  # SOL to wallet
                amount_tokens,
                min_amount_out,
                is_sol_to_token=False
            )
            
            # 6. Create and send transaction
            tx = Transaction().add(swap_ix)
            
            result = self._send_and_confirm_transaction(tx)
            if result:
                print(f"Successfully sold {token.symbol}")
                print(f"Expected output: {amount_out / 1e9:.6f} SOL")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error selling token: {str(e)}")
            return False

    def _send_and_confirm_transaction(self, transaction: Transaction) -> bool:
        """
        Signs, sends, and confirms a transaction
        """
        try:
            # Sign transaction
            transaction.sign(self.wallet)
            
            # Send transaction
            result = self.rpc_client.send_transaction(
                transaction,
                self.wallet,
                opts={"skip_confirmation": False, "preflight_commitment": CommitmentLevel.Confirmed}
            )
            
            if "error" in result:
                print(f"Transaction failed: {result['error']}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Transaction failed: {str(e)}")
            return False

    def _get_token_balance(self, token_address: str) -> int:
        """
        Gets the token balance for the wallet
        """
        try:
            token_account = get_associated_token_address(
                self.wallet.public_key,
                Pubkey(token_address)
            )
            response = self.rpc_client.get_token_account_balance(str(token_account))
            if "result" in response:
                return int(response["result"]["amount"])
            return 0
        except Exception:
            return 0