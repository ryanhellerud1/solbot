import pytest
from src.config import Config, Network

def test_default_network():
    """Test that the default network is devnet"""
    Config._instance = None  # Reset singleton
    config = Config()
    assert config._current_network == Network.DEVNET

def test_network_change():
    """Test network change functionality"""
    Config._instance = None  # Reset singleton
    Config.set_network(Network.MAINNET)
    assert Config.get_network() == Network.MAINNET
    
def test_rpc_url():
    """Test RPC URL generation"""
    Config._instance = None  # Reset singleton
    Config.set_network(Network.DEVNET)
    assert Config.get_rpc_url() == "https://api.devnet.solana.com"
    
    Config.set_network(Network.MAINNET)
    assert Config.get_rpc_url() == "https://api.mainnet-beta.solana.com"

def test_custom_rpc():
    """Test custom RPC URL setting"""
    Config._instance = None  # Reset singleton
    custom_url = "https://my-custom-rpc.solana.com"
    Config.set_custom_rpc(custom_url)
    assert Config.get_rpc_url() == custom_url 