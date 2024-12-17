from dataclasses import dataclass
from datetime import datetime
from typing import List, Set, Optional, Callable
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solana.rpc.commitment import Confirmed
from solana.rpc.websocket_api import connect
from config import Config, Network
import base58
import json
import time
import asyncio
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TokenInfo:
    address: str
    name: str
    symbol: str
    decimals: int
    total_supply: int
    creation_time: datetime
    initial_liquidity: float
    metadata_url: Optional[str] = None

class TokenScanner:
    TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
    METADATA_PROGRAM_ID = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")
    SYSTEM_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")
    
    def __init__(self, rpc_client: Client):
        self.rpc_client = rpc_client
        self.last_scan_time = datetime.now()
        self.known_tokens: Set[str] = set()
        self.ws_url = Config.get_rpc_url().replace('https://', 'wss://').replace('http://', 'ws://')
        self.token_callback: Optional[Callable[[TokenInfo], None]] = None

    async def _process_transaction(self, tx_sig: str) -> Optional[TokenInfo]:
        try:
            tx_response = self.rpc_client.get_transaction(
                tx_sig,
                encoding="jsonParsed",
                max_supported_transaction_version=0
            )
            
            if not tx_response.value:
                return None
                
            tx = tx_response.value
            
            if hasattr(tx, 'meta') and tx.meta and hasattr(tx.transaction, 'message'):
                message = tx.transaction.message
                
                for idx, instruction in enumerate(message.instructions):
                    if hasattr(instruction, 'parsed'):
                        parsed = instruction.parsed
                        if isinstance(parsed, dict):
                            if parsed.get('type') == 'initializeMint':
                                mint_address = parsed.get('info', {}).get('mint')
                                if mint_address and mint_address not in self.known_tokens:
                                    logger.info(f"Found new token creation: {mint_address}")
                                    token_info = await self._get_token_info(mint_address)
                                    if token_info:
                                        self.known_tokens.add(mint_address)
                                        return token_info
            return None
            
        except Exception as e:
            logger.error(f"Error processing transaction {tx_sig}: {str(e)}")
            return None

    async def _get_token_info(self, token_address: str) -> Optional[TokenInfo]:
        try:
            pubkey = Pubkey.from_string(token_address)
            account_info = self.rpc_client.get_account_info(pubkey)
            
            if not account_info.value:
                return None

            name, symbol, metadata_url = await self._get_token_metadata(token_address)

            try:
                slot = self.rpc_client.get_slot().value
                block_time = self.rpc_client.get_block_time(slot).value
                creation_time = datetime.fromtimestamp(block_time)
            except Exception as e:
                logger.error(f"Error getting creation time: {str(e)}")
                creation_time = datetime.now()

            try:
                supply_info = self.rpc_client.get_token_supply(pubkey)
                total_supply = int(supply_info.value.amount) if supply_info.value else 0
            except Exception as e:
                logger.error(f"Error getting supply: {str(e)}")
                total_supply = 0

            try:
                from raydium_dex import RaydiumDEX
                pool_info = RaydiumDEX.get_pool_info(self.rpc_client, token_address)
                initial_liquidity = pool_info.quote_reserve / 1e9 if pool_info else 0.0
            except Exception as e:
                logger.error(f"Error getting liquidity: {str(e)}")
                initial_liquidity = 0.0

            return TokenInfo(
                address=token_address,
                name=name,
                symbol=symbol,
                decimals=9,
                total_supply=total_supply,
                creation_time=creation_time,
                initial_liquidity=initial_liquidity,
                metadata_url=metadata_url
            )
            
        except Exception as e:
            logger.error(f"Error getting token info: {str(e)}")
            return None

    async def _get_token_metadata(self, mint_address: str) -> tuple[str, str, str]:
        try:
            metadata_address = self._get_metadata_pda(mint_address)
            if not metadata_address:
                return "Unknown", "UNKNOWN", None

            metadata_account = self.rpc_client.get_account_info(
                metadata_address,
                encoding="base64"
            )

            if not metadata_account.value:
                return "Unknown", "UNKNOWN", None

            try:
                data = metadata_account.value.data
                if not data:
                    return "Unknown", "UNKNOWN", None

                name_len = int.from_bytes(data[8:12], byteorder='little')
                name = data[12:12+name_len].decode('utf-8').strip('\x00')
                
                symbol_len = int.from_bytes(data[12+name_len:12+name_len+4], byteorder='little')
                symbol = data[12+name_len+4:12+name_len+4+symbol_len].decode('utf-8').strip('\x00')
                
                uri_len = int.from_bytes(data[12+name_len+4+symbol_len:12+name_len+4+symbol_len+4], byteorder='little')
                uri = data[12+name_len+4+symbol_len+4:12+name_len+4+symbol_len+4+uri_len].decode('utf-8').strip('\x00')
                
                return name, symbol, uri
            except Exception as e:
                logger.error(f"Error parsing metadata: {str(e)}")
                return "Unknown", "UNKNOWN", None

        except Exception as e:
            logger.error(f"Error getting token metadata: {str(e)}")
            return "Unknown", "UNKNOWN", None

    def _get_metadata_pda(self, mint_address: str) -> Optional[Pubkey]:
        try:
            seeds = [
                b"metadata",
                bytes(self.METADATA_PROGRAM_ID),
                bytes(Pubkey.from_string(mint_address))
            ]
            metadata_address, _ = Pubkey.find_program_address(
                seeds,
                self.METADATA_PROGRAM_ID
            )
            return metadata_address
        except Exception as e:
            logger.error(f"Error getting metadata PDA: {str(e)}")
            return None

    async def listen_for_tokens(self, callback: Optional[Callable[[TokenInfo], None]] = None):
        self.token_callback = callback
        
        async def handle_transaction(tx_sig: str):
            token_info = await self._process_transaction(tx_sig)
            if token_info:
                if self.token_callback:
                    self.token_callback(token_info)
                else:
                    logger.info(f"\nNew token detected!")
                    logger.info(f"Address: {token_info.address}")
                    logger.info(f"Name: {token_info.name}")
                    logger.info(f"Symbol: {token_info.symbol}")
                    logger.info(f"Creation Time: {token_info.creation_time}")
                    logger.info(f"Initial Liquidity: {token_info.initial_liquidity} SOL")
                    if token_info.metadata_url:
                        logger.info(f"Metadata URL: {token_info.metadata_url}")
                    logger.info("-" * 50)

        async def subscribe_to_program():
            while True:
                try:
                    async with websockets.connect(self.ws_url) as websocket:
                        logger.info(f"Listening for new token creations...")
                        logger.info(f"Connected to {self.ws_url}")
                        
                        # Subscribe to Token Program logs
                        token_subscribe_message = {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "programSubscribe",
                            "params": [
                                str(self.TOKEN_PROGRAM_ID),
                                {
                                    "encoding": "jsonParsed",
                                    "commitment": "confirmed",
                                    "filters": [
                                        {
                                            "memcmp": {
                                                "offset": 0,
                                                "bytes": "3"  # InitializeMint instruction
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                        
                        logger.info(f"Subscribing to Token Program: {str(self.TOKEN_PROGRAM_ID)}")
                        await websocket.send(json.dumps(token_subscribe_message))
                        
                        response = await websocket.recv()
                        response_data = json.loads(response)
                        if "error" in response_data:
                            logger.error(f"Token Program subscription error: {response_data['error']}")
                        else:
                            logger.info(f"Token Program subscription successful: {response}")

                        # Also subscribe to System Program for account creation
                        system_subscribe_message = {
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "programSubscribe",
                            "params": [
                                str(self.SYSTEM_PROGRAM_ID),
                                {
                                    "encoding": "jsonParsed",
                                    "commitment": "confirmed",
                                    "filters": [
                                        {
                                            "dataSize": 82  # Size of token mint accounts
                                        }
                                    ]
                                }
                            ]
                        }
                        
                        logger.info(f"Subscribing to System Program for account creation")
                        await websocket.send(json.dumps(system_subscribe_message))
                        
                        response = await websocket.recv()
                        response_data = json.loads(response)
                        if "error" in response_data:
                            logger.error(f"System Program subscription error: {response_data['error']}")
                        else:
                            logger.info(f"System Program subscription successful: {response}")

                        logger.info("Monitoring for token creations (this may take a few minutes)...")
                        logger.info("Press Ctrl+C to stop")
                        
                        async for msg in websocket:
                            try:
                                data = json.loads(msg)
                                logger.debug(f"Received message: {json.dumps(data, indent=2)}")
                                
                                if 'params' in data:
                                    result = data['params'].get('result', {})
                                    if isinstance(result, dict):
                                        # For program subscription messages
                                        if 'value' in result:
                                            value = result['value']
                                            pubkey = value.get('pubkey')
                                            logger.debug(f"Processing program activity for account: {pubkey}")
                                            
                                            # Check if this is a token mint account
                                            if value.get('data') and value.get('owner') == str(self.TOKEN_PROGRAM_ID):
                                                logger.info(f"Potential token mint account created: {pubkey}")
                                                await handle_transaction(pubkey)
                                        
                                        # For transaction logs
                                        elif 'signature' in result:
                                            signature = result['signature']
                                            logger.debug(f"Processing transaction: {signature}")
                                            
                                            # Get full transaction details
                                            tx_response = self.rpc_client.get_transaction(
                                                signature,
                                                encoding="jsonParsed",
                                                max_supported_transaction_version=0
                                            )
                                            
                                            if tx_response.value:
                                                tx = tx_response.value
                                                if hasattr(tx, 'meta') and tx.meta:
                                                    for log in tx.meta.log_messages or []:
                                                        if any(pattern in log for pattern in [
                                                            "Initialize mint",
                                                            "Create mint",
                                                            "Token program: initialize mint",
                                                            "Creating mint account"
                                                        ]):
                                                            logger.info(f"Found token creation in transaction {signature}")
                                                            logger.info(f"Log message: {log}")
                                                            await handle_transaction(signature)
                                                            break
                            except json.JSONDecodeError as e:
                                logger.error(f"Error decoding message: {str(e)}")
                                continue
                            except Exception as e:
                                logger.error(f"Error processing message: {str(e)}")
                                logger.debug("Error details:", exc_info=True)
                                continue
                                
                except websockets.exceptions.ConnectionClosed as e:
                    logger.error(f"WebSocket connection closed: {str(e)}")
                    logger.info("Reconnecting in 5 seconds...")
                    await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"WebSocket error: {str(e)}")
                    logger.debug("Error details:", exc_info=True)
                    logger.info("Reconnecting in 5 seconds...")
                    await asyncio.sleep(5)

        await subscribe_to_program()

def run_token_scanner():
    scanner = TokenScanner(Client(Config.get_rpc_url()))
    
    async def main():
        await scanner.listen_for_tokens()
    
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("\nStopping token scanner...")
    except Exception as e:
        logger.error(f"Error running token scanner: {str(e)}")
        import traceback
        traceback.print_exc()
