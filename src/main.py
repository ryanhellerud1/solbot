import os
import time
import logging
from dotenv import load_dotenv
from solders.keypair import Keypair
from solana.rpc.api import Client
from scanner import TokenScanner
from risk_analyzer import RiskAnalyzer
from token_buyer import TokenBuyer
from config import Config, Network
import argparse
import base58

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_network_connection(rpc_client):
    """Test if we can connect to the network"""
    try:
        version = rpc_client.get_version()
        logger.info(f"Successfully connected to Solana {Config.get_network().value}")
        logger.info(f"Node version: {version}")
        return True
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return False

def check_wallet_balance(rpc_client, wallet):
    """Check wallet SOL balance"""
    try:
        balance = rpc_client.get_balance(wallet.pubkey())
        balance_sol = balance.value / 1e9  # Convert lamports to SOL
        logger.info(f"Wallet balance: {balance_sol:.4f} SOL")
        return balance_sol
    except Exception as e:
        logger.error(f"Failed to get wallet balance: {str(e)}")
        return 0

def create_keypair_from_private_key(private_key_b58: str):
    """Create a Keypair from a base58 private key"""
    try:
        # Decode base58 private key
        private_key_bytes = base58.b58decode(private_key_b58)
        return Keypair.from_bytes(private_key_bytes)
    except Exception as e:
        logger.error(f"Failed to create keypair: {str(e)}")
        return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Solana Token Scanner and Trader')
    parser.add_argument('--network', choices=['mainnet', 'devnet'], default='mainnet',
                       help='Network to connect to (default: mainnet)')
    parser.add_argument('--rpc-url', type=str, help='Custom RPC URL (optional)')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode')
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Configure network
    if args.rpc_url:
        Config.set_custom_rpc(args.rpc_url)
    else:
        Config.set_network(Network.DEVNET if args.network == 'devnet' else Network.MAINNET)

    # Initialize RPC client
    rpc_client = Client(Config.get_rpc_url())
    
    # Create wallet from private key
    private_key = os.getenv('WALLET_PRIVATE_KEY')
    if not private_key:
        logger.error("No wallet private key found in .env file")
        return
        
    wallet = create_keypair_from_private_key(private_key)
    if not wallet:
        logger.error("Failed to create wallet from private key")
        return
    
    logger.info(f"Starting token scanner on {Config.get_network().value}")
    logger.info(f"RPC URL: {Config.get_rpc_url()}")
    logger.info(f"Wallet address: {wallet.pubkey()}")

    # Test network connection
    if not test_network_connection(rpc_client):
        logger.error("Failed to connect to network. Exiting...")
        return

    # Initialize scanner
    scanner = TokenScanner(rpc_client)
    scan_count = 0

    logger.info("Starting continuous token scanning. Press Ctrl+C to stop.")
    logger.info("Watching for new token creations...")

    while True:
        try:
            scan_count += 1
            logger.info(f"\nScan #{scan_count} - Looking for new tokens...")
            
            # Scan for new tokens
            new_tokens = scanner.scan_new_tokens()
            
            if new_tokens:
                logger.info(f"Found {len(new_tokens)} new tokens!")
                
                for token in new_tokens:
                    logger.info("\n=== New Token Detected ===")
                    logger.info(f"Address: {token.address}")
                    logger.info(f"Name: {token.name}")
                    logger.info(f"Symbol: {token.symbol}")
                    logger.info(f"Decimals: {token.decimals}")
                    logger.info(f"Total Supply: {token.total_supply}")
                    logger.info(f"Creation Time: {token.creation_time}")
                    logger.info(f"Initial Liquidity: {token.initial_liquidity} SOL")
                    logger.info("=====================")
            else:
                logger.info("No new tokens found in this scan")
            
            # Sleep to avoid rate limiting
            sleep_time = 5
            logger.info(f"Waiting {sleep_time} seconds before next scan...")
            time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("\nStopping token scanner...")
            break
        except Exception as e:
            logger.error(f"Error during scan: {str(e)}")
            time.sleep(5)  # Wait a bit before retrying

if __name__ == "__main__":
    main() 