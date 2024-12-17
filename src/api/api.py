from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('bot.log')  # Log to file
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner import TokenScanner
from token_buyer import TokenBuyer
from config import Config, Network
from trading_strategy import TradeSignal

app = FastAPI(title="Solana Trading Bot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class BotStatus(BaseModel):
    is_running: bool
    network: str
    wallet_balance: float
    tokens_scanned: int
    active_trades: int

class TokenData(BaseModel):
    address: str
    symbol: str
    price: float
    volume_24h: float
    price_change_1h: float

class TradeData(BaseModel):
    token_address: str
    type: str  # "buy" or "sell"
    amount: float
    status: str
    timestamp: str

# Global bot state
bot_state = {
    "is_running": False,
    "tokens_scanned": 0,
    "active_trades": 0,
    "start_time": None,
    "last_scan_time": None
}

@app.get("/")
async def root():
    return {"status": "Bot API is running"}

@app.get("/status", response_model=BotStatus)
async def get_status():
    try:
        # Get wallet balance
        client = Config.get_client()
        wallet = Config.get_wallet()
        balance = client.get_balance(wallet.pubkey()).value / 1e9
        
        # Log detailed information
        logger.info(f"Network: {Config.get_network().value}")
        logger.info(f"RPC URL: {Config.get_rpc_url()}")
        logger.info(f"Wallet Address: {wallet.pubkey()}")
        logger.info(f"Current Balance: {balance:.4f} SOL")

        # Add runtime information to log
        if bot_state["is_running"] and bot_state["start_time"]:
            runtime = datetime.now() - bot_state["start_time"]
            logger.info(f"Bot running for: {runtime}")

        status = BotStatus(
            is_running=bot_state["is_running"],
            network=Config.get_network().value,
            wallet_balance=balance,
            tokens_scanned=bot_state["tokens_scanned"],
            active_trades=bot_state["active_trades"]
        )
        
        logger.info(f"Returning status: {status}")
        return status
        
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start")
async def start_bot():
    try:
        if not bot_state["is_running"]:
            bot_state["is_running"] = True
            bot_state["start_time"] = datetime.now()
            logger.info(f"Bot started at {bot_state['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Network: {Config.get_network().value}")
            
            # Get and log initial wallet balance
            client = Config.get_client()
            wallet = Config.get_wallet()
            balance = client.get_balance(wallet.pubkey()).value / 1e9
            logger.info(f"Initial wallet balance: {balance:.4f} SOL")
            
            return {"status": "Bot started successfully"}
        return {"status": "Bot is already running"}
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop")
async def stop_bot():
    try:
        if bot_state["is_running"]:
            stop_time = datetime.now()
            runtime = stop_time - bot_state["start_time"] if bot_state["start_time"] else None
            
            bot_state["is_running"] = False
            bot_state["start_time"] = None
            
            logger.info(f"Bot stopped at {stop_time.strftime('%Y-%m-%d %H:%M:%S')}")
            if runtime:
                logger.info(f"Total runtime: {runtime}")
            logger.info(f"Total tokens scanned: {bot_state['tokens_scanned']}")
            
            # Get and log final wallet balance
            client = Config.get_client()
            wallet = Config.get_wallet()
            balance = client.get_balance(wallet.pubkey()).value / 1e9
            logger.info(f"Final wallet balance: {balance:.4f} SOL")
            
            return {"status": "Bot stopped successfully"}
        return {"status": "Bot is already stopped"}
    except Exception as e:
        logger.error(f"Error stopping bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tokens", response_model=List[TokenData])
async def get_tokens():
    try:
        if bot_state["is_running"]:
            bot_state["last_scan_time"] = datetime.now()
            logger.info(f"Scanning for tokens at {bot_state['last_scan_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        return []  # Return actual token data when implemented
    except Exception as e:
        logger.error(f"Error getting tokens: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trades", response_model=List[TradeData])
async def get_trades():
    try:
        return []  # Return actual trade data when implemented
    except Exception as e:
        logger.error(f"Error getting trades: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/network/{network}")
async def set_network(network: str):
    try:
        if network not in ["mainnet", "devnet"]:
            raise HTTPException(status_code=400, detail="Invalid network")
        Config.set_network(Network.DEVNET if network == "devnet" else Network.MAINNET)
        logger.info(f"Network changed to {network}")
        return {"status": f"Network changed to {network}"}
    except Exception as e:
        logger.error(f"Error changing network: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Solana Trading Bot API")
    uvicorn.run(app, host="0.0.0.0", port=8000) 