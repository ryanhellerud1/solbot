import logging
from scanner import TokenScanner, TokenInfo, run_token_scanner
from solana.rpc.api import Client
from config import Config, Network

# Configure logging with debug level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def token_callback(token: TokenInfo):
    """Custom callback for new token events"""
    logger.info(f"\n🪙 New Token Created!")
    logger.info(f"Address: {token.address}")
    logger.info(f"Name: {token.name}")
    logger.info(f"Symbol: {token.symbol}")
    logger.info(f"Creation Time: {token.creation_time}")
    logger.info(f"Initial Liquidity: {token.initial_liquidity} SOL")
    if token.metadata_url:
        logger.info(f"Metadata URL: {token.metadata_url}")
    logger.info("-" * 50)

def verify_connection():
    """Verify RPC connection and network settings"""
    try:
        # Check network setting
        network = Config.get_network()
        logger.info(f"Network setting: {network.value}")
        
        # Check RPC URL
        rpc_url = Config.get_rpc_url()
        logger.info(f"RPC URL: {rpc_url}")
        
        # Test RPC connection
        client = Client(rpc_url)
        version = client.get_version()
        logger.info(f"Connected to Solana {version.value.solana_core}")
        
        # Get recent block to verify we can read from chain
        slot = client.get_slot().value
        logger.info(f"Current slot: {slot}")
        
        return True
    except Exception as e:
        logger.error(f"Connection verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Initialize RPC client for mainnet
    Config.set_network(Network.MAINNET)
    
    # Verify connection
    logger.info("Verifying connection...")
    if not verify_connection():
        logger.error("Failed to verify connection. Exiting.")
        exit(1)
    
    # Run the token scanner
    logger.info("\nStarting WebSocket token scanner...")
    logger.info("Press Ctrl+C to stop")
    
    # Run the scanner
    run_token_scanner() 