import logging
from solana.rpc.api import Client
from scanner import TokenScanner
from config import Config, Network

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Initialize RPC client for mainnet
    Config.set_network(Network.MAINNET)
    rpc_client = Client(Config.get_rpc_url())
    
    # Initialize scanner
    scanner = TokenScanner(rpc_client)
    
    logger.info("Starting token scan on mainnet...")
    new_tokens = scanner.scan_new_tokens()
    
    if new_tokens:
        logger.info(f"Found {len(new_tokens)} new tokens:")
        for token in new_tokens:
            logger.info(f"Token Address: {token.address}")
            logger.info(f"Name: {token.name}")
            logger.info(f"Symbol: {token.symbol}")
            logger.info(f"Creation Time: {token.creation_time}")
            logger.info(f"Initial Liquidity: {token.initial_liquidity} SOL")
            logger.info("-" * 50)
    else:
        logger.info("No new tokens found in this scan")

if __name__ == "__main__":
    main() 