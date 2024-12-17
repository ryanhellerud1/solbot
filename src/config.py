from enum import Enum
from typing import Optional
from solana.rpc.api import Client
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Network(Enum):
    MAINNET = "mainnet"
    DEVNET = "devnet"

class Config:
    # Default RPC endpoints
    RPC_URLS = {
        Network.MAINNET: "https://api.mainnet-beta.solana.com",
        Network.DEVNET: "https://api.devnet.solana.com"
    }
    
    _instance = None
    _current_network: Network = Network.DEVNET  # Default to devnet
    _custom_rpc_url: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from environment variables"""
        load_dotenv()
        
        # Load RPC URL from environment or use default
        self._custom_rpc_url = os.getenv('SOLANA_RPC_URL')
        
        # Set network based on RPC URL or environment variable
        network = os.getenv('SOLANA_NETWORK', 'devnet').lower()
        if network == 'mainnet' or (self._custom_rpc_url and "mainnet" in self._custom_rpc_url.lower()):
            self._current_network = Network.MAINNET
        else:
            self._current_network = Network.DEVNET
            
        logger.info(f"Initialized with network: {self._current_network.value}")
    
    @classmethod
    def set_network(cls, network: Network):
        """Manually set the network"""
        instance = cls()
        instance._current_network = network
        instance._custom_rpc_url = None  # Reset custom URL when changing network
        logger.info(f"Network changed to {network.value}")
        
        # Verify wallet balance after network change
        cls.verify_wallet_balance()
    
    @classmethod
    def set_custom_rpc(cls, rpc_url: str):
        """Set a custom RPC URL"""
        instance = cls()
        instance._custom_rpc_url = rpc_url
        # Update network based on URL
        if "devnet" in rpc_url.lower():
            instance._current_network = Network.DEVNET
        else:
            instance._current_network = Network.MAINNET
        logger.info(f"Custom RPC URL set for {instance._current_network.value}")
        
        # Verify wallet balance after RPC change
        cls.verify_wallet_balance()
    
    @classmethod
    def get_rpc_url(cls) -> str:
        """Get the current RPC URL"""
        instance = cls()
        if instance._custom_rpc_url:
            return instance._custom_rpc_url
        return cls.RPC_URLS[instance._current_network]
    
    @classmethod
    def get_client(cls) -> Client:
        """Get a configured Solana client"""
        return Client(cls.get_rpc_url())
    
    @classmethod
    def is_devnet(cls) -> bool:
        """Check if currently on devnet"""
        instance = cls()
        return instance._current_network == Network.DEVNET
    
    @classmethod
    def get_network(cls) -> Network:
        """Get current network"""
        instance = cls()
        return instance._current_network
    
    @classmethod
    def get_wallet(cls):
        """Get the configured wallet"""
        from main import create_keypair_from_private_key
        import os
        
        private_key = os.getenv('WALLET_PRIVATE_KEY')
        if not private_key:
            raise Exception("No wallet private key found in .env file")
            
        wallet = create_keypair_from_private_key(private_key)
        if not wallet:
            raise Exception("Failed to create wallet from private key")
            
        return wallet
    
    @classmethod
    def verify_wallet_balance(cls):
        """Verify and log the wallet balance"""
        try:
            client = cls.get_client()
            wallet = cls.get_wallet()
            balance = client.get_balance(wallet.pubkey()).value / 1e9
            logger.info(f"Wallet balance on {cls.get_network().value}: {balance:.4f} SOL")
            return balance
        except Exception as e:
            logger.error(f"Error verifying wallet balance: {str(e)}")
            return 0