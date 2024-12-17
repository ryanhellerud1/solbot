# Solana Token Scanner Bot

A real-time token scanner and trading bot for the Solana blockchain. This bot monitors new token creations, analyzes their potential, and can execute trades based on configurable strategies.

## Features

- Real-time token creation monitoring using WebSocket subscriptions
- Token metadata and liquidity analysis
- Support for both Mainnet and Devnet
- Web interface for monitoring and control
- Automatic trading capabilities (configurable)
- Detailed logging and transaction history

## Prerequisites

- Python 3.9+
- Node.js 16+ (for frontend)
- Solana CLI tools
- A Solana wallet with some SOL for transactions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crypto-bot.git
cd crypto-bot
```

2. Set up the Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd src/frontend
npm install
```

4. Create a `.env` file in the root directory:
```bash
WALLET_PRIVATE_KEY=your_private_key_here
SOLANA_NETWORK=mainnet  # or devnet
SOLANA_RPC_URL=your_rpc_url_here  # Optional: custom RPC URL
```

## Usage

1. Start the backend API:
```bash
cd src
uvicorn api.api:app --reload
```

2. Start the frontend development server:
```bash
cd src/frontend
npm run dev
```

3. Run the token scanner:
```bash
python src/test_ws_scanner.py
```

## Configuration

- Network settings can be changed in `src/config.py`
- Trading parameters can be adjusted in `src/token_buyer.py`
- Frontend configuration is in `src/frontend/src/App.tsx`

## Architecture

- `src/scanner.py`: Token detection and analysis
- `src/token_buyer.py`: Trading logic
- `src/config.py`: Configuration management
- `src/api/`: FastAPI backend
- `src/frontend/`: React frontend

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

- Never commit your private keys or sensitive information
- Use environment variables for sensitive data
- Be careful with RPC endpoints and rate limits
- Monitor your wallet activity regularly

## Disclaimer

This bot is for educational purposes only. Cryptocurrency trading carries significant risks. Always do your own research and never trade with funds you can't afford to lose. 