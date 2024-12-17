from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from scanner import TokenInfo

@dataclass
class MarketMetrics:
    price: float
    volume_24h: float
    market_cap: float
    liquidity: float
    price_change_1h: float
    price_change_5m: float  # Added shorter timeframe
    holder_count: int
    top_holder_percentage: float  # Added concentration metric
    creator_wallet_balance: float  # Track creator's wallet
    time_since_creation: timedelta
    liquidity_locked: bool
    initial_liquidity_amount: float

@dataclass
class TradeSignal:
    should_buy: bool
    should_sell: bool
    confidence: float  # 0 to 1
    reason: str
    suggested_position_size: float  # in SOL

class TradingStrategy:
    def __init__(self):
        # Rug pull protection parameters
        self.max_creator_wallet_percentage = 0.05  # Max 5% of supply
        self.max_single_wallet_percentage = 0.03   # Max 3% of supply (excluding LP)
        self.min_locked_liquidity = 0.95          # 95% of liquidity should be locked
        self.min_initial_liquidity_sol = 5.0      # Minimum 5 SOL initial liquidity
        
        # Sniper parameters
        self.max_token_age = timedelta(minutes=30)  # Only tokens < 30 mins old
        self.min_price_increase_5m = 0.20          # 20% minimum pump in 5 mins
        self.max_price_increase_5m = 2.0           # 200% maximum pump (avoid fake pumps)
        
        # Quick profit targets
        self.initial_take_profit = 0.5     # +50% first target
        self.extended_take_profit = 1.0    # +100% if momentum continues
        self.stop_loss = -0.1              # -10% stop loss (tight)
        self.trailing_stop = 0.15          # 15% trailing stop once in profit
        
        # Position sizing
        self.max_position_size = 0.1       # Maximum 0.1 SOL per trade
        self.risk_per_trade = 0.05         # 5% risk per trade (aggressive)

    def analyze_buy_opportunity(self, token: TokenInfo, metrics: MarketMetrics) -> TradeSignal:
        """
        Analyzes if we should snipe this token based on early signals and safety checks.
        """
        # Immediate disqualifiers (rug pull protection)
        if self._is_potential_rug_pull(metrics):
            return TradeSignal(False, False, 0, "Rug pull risk detected", 0)

        # Only look at very new tokens
        if metrics.time_since_creation > self.max_token_age:
            return TradeSignal(False, False, 0, "Token too old for sniping", 0)

        reasons = []
        confidence_scores = []

        # 1. Liquidity Check (must have minimum liquidity)
        if metrics.initial_liquidity_amount < self.min_initial_liquidity_sol:
            return TradeSignal(False, False, 0, "Insufficient initial liquidity", 0)
        
        # 2. Early Pump Detection
        if self.min_price_increase_5m <= metrics.price_change_5m <= self.max_price_increase_5m:
            confidence_scores.append(0.9)
            reasons.append(f"Strong early momentum: {metrics.price_change_5m:.1%}")
        
        # 3. Holder Analysis
        if 10 <= metrics.holder_count <= 100:  # Sweet spot for early entry
            confidence_scores.append(0.8)
            reasons.append("Optimal early holder count")
        
        # 4. Liquidity Lock Status
        if metrics.liquidity_locked:
            confidence_scores.append(0.7)
            reasons.append("Liquidity locked")

        # Calculate final confidence and position size
        if not confidence_scores:
            return TradeSignal(False, False, 0, "No strong buy signals", 0)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        position_size = self._calculate_position_size(avg_confidence, metrics.price)
        
        return TradeSignal(
            should_buy=avg_confidence > 0.7,  # Higher confidence threshold for sniping
            should_sell=False,
            confidence=avg_confidence,
            reason=" | ".join(reasons),
            suggested_position_size=position_size
        )

    def analyze_sell_opportunity(self, token: TokenInfo, metrics: MarketMetrics, 
                               entry_price: float, highest_price: float) -> TradeSignal:
        """
        Quick profit-taking and tight stop-loss strategy
        """
        current_price = metrics.price
        price_change = (current_price - entry_price) / entry_price
        trailing_stop_price = highest_price * (1 - self.trailing_stop)
        
        reasons = []
        should_sell = False

        # 1. Stop Loss (tight)
        if price_change <= self.stop_loss:
            should_sell = True
            reasons.append(f"Stop loss triggered: {price_change:.1%}")

        # 2. Take Profit Stages
        elif price_change >= self.extended_take_profit:
            should_sell = True
            reasons.append(f"Extended profit target reached: {price_change:.1%}")
        elif price_change >= self.initial_take_profit:
            # Check if momentum is slowing
            if metrics.price_change_5m < 0.05:
                should_sell = True
                reasons.append(f"Initial profit target with slowing momentum: {price_change:.1%}")

        # 3. Trailing Stop (only if in profit)
        elif price_change > 0 and current_price < trailing_stop_price:
            should_sell = True
            reasons.append(f"Trailing stop triggered at {price_change:.1%} profit")

        # 4. Rug Pull Detection (emergency sell)
        if self._is_potential_rug_pull(metrics):
            should_sell = True
            reasons.append("Rug pull warning signals detected")

        return TradeSignal(
            should_buy=False,
            should_sell=should_sell,
            confidence=0.9 if should_sell else 0,
            reason=" | ".join(reasons) if reasons else "No sell signals",
            suggested_position_size=0
        )

    def _is_potential_rug_pull(self, metrics: MarketMetrics) -> bool:
        """
        Checks for common rug pull signals
        """
        return any([
            metrics.top_holder_percentage > self.max_single_wallet_percentage,
            metrics.creator_wallet_balance > self.max_creator_wallet_percentage,
            not metrics.liquidity_locked and metrics.time_since_creation > timedelta(minutes=10),
            metrics.price_change_5m > 5.0  # Suspicious pump (>500%)
        ])

    def _calculate_position_size(self, confidence: float, current_price: float) -> float:
        """
        Calculates the position size based on confidence and risk parameters
        """
        # More aggressive position sizing for high-confidence trades
        position_size = self.max_position_size * confidence
        
        # Adjust for risk per trade
        risk_adjusted_size = position_size * self.risk_per_trade
        
        return min(risk_adjusted_size, self.max_position_size) 