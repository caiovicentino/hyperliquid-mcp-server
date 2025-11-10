"""MCP Server for Hyperliquid Trading Platform."""
import os
import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP, Context
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from eth_account import Account

from tools import TradingTools, AccountTools, MarketTools, WebSocketTools
from config.hyperliquid_config import (
    API_URL,
    WS_URL,
    PRIVATE_KEY,
    ACCOUNT_ADDRESS,
    NETWORK,
    validate_config,
    get_config_summary
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variable to store application context
app_context: Optional[AppContext] = None


@dataclass
class AppContext:
    """Application context with tool instances and SDK clients."""
    info_client: Info
    exchange_client: Exchange
    trading_tools: TradingTools
    account_tools: AccountTools
    market_tools: MarketTools
    websocket_tools: WebSocketTools
    account_address: str
    network: str


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Manage application lifecycle with Hyperliquid SDK initialization.

    This function:
    1. Validates environment configuration
    2. Initializes Hyperliquid Info and Exchange clients
    3. Creates tool instances
    4. Yields application context
    5. Handles cleanup on shutdown
    """
    # Validate configuration
    is_valid, error_message = validate_config()
    if not is_valid:
        raise ValueError(f"Configuration validation failed: {error_message}")

    logger.info("Starting Hyperliquid MCP Server...")
    logger.info(get_config_summary())

    try:
        # Initialize Hyperliquid SDK clients
        logger.info(f"Initializing Hyperliquid clients for {NETWORK}...")

        # Info client for reading market data and account info
        info_client = Info(API_URL, skip_ws=True)

        # Exchange client for trading operations
        # Create wallet from private key for signing transactions
        wallet = Account.from_key(PRIVATE_KEY)
        exchange_client = Exchange(
            wallet=wallet,
            base_url=API_URL,
            account_address=ACCOUNT_ADDRESS
        )

        logger.info(f"Connected to Hyperliquid {NETWORK}")
        logger.info(f"Account: {ACCOUNT_ADDRESS[:6]}...{ACCOUNT_ADDRESS[-4:]}")

        # Initialize tool instances
        trading_tools = TradingTools(exchange_client, info_client, ACCOUNT_ADDRESS)
        account_tools = AccountTools(info_client, ACCOUNT_ADDRESS)
        market_tools = MarketTools(info_client, ACCOUNT_ADDRESS)
        websocket_tools = WebSocketTools(WS_URL, ACCOUNT_ADDRESS)

        logger.info("All tools initialized successfully")

        # Create and store application context globally
        global app_context
        app_context = AppContext(
            info_client=info_client,
            exchange_client=exchange_client,
            trading_tools=trading_tools,
            account_tools=account_tools,
            market_tools=market_tools,
            websocket_tools=websocket_tools,
            account_address=ACCOUNT_ADDRESS,
            network=NETWORK
        )

        # Yield application context
        yield app_context

    except Exception as e:
        logger.error(f"Failed to initialize Hyperliquid clients: {e}")
        raise

    finally:
        # Cleanup on shutdown
        logger.info("Shutting down Hyperliquid MCP Server...")
        # Add any cleanup logic here (close connections, etc.)


# Create MCP server
mcp = FastMCP(
    "hyperliquid-mcp-server",
    dependencies=["hyperliquid-python-sdk", "eth-account", "python-dotenv"],
    lifespan=app_lifespan
)


# ============================================================================
# TRADING TOOLS (9 methods)
# ============================================================================

@mcp.tool()
async def place_order(
    coin: str,
    is_buy: bool,
    size: float,
    price: float,
    order_type: str = "limit",
    tif: str = "Gtc",
    reduce_only: bool = False,
    cloid: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Place a single order on Hyperliquid.

    Args:
        coin: Trading pair symbol (e.g., "BTC", "ETH")
        is_buy: True for buy order, False for sell order
        size: Order size in base currency units
        price: Limit price (ignored for market orders)
        order_type: "limit" or "market"
        tif: Time in force - "Gtc", "Ioc", "Alo"
        reduce_only: If True, order can only reduce existing position
        cloid: Client order ID for tracking (optional)

    Returns:
        Order placement result with order ID and status
    """
    if ctx:
        if ctx: ctx.info(f"Placing {'buy' if is_buy else 'sell'} {order_type} order: {size} {coin} @ {price}")

    result = await app_context.trading_tools.place_order(
        coin=coin,
        is_buy=is_buy,
        size=size,
        price=price,
        order_type=order_type,
        tif=tif,
        reduce_only=reduce_only,
        cloid=cloid
    )
    return result


@mcp.tool()
async def place_batch_orders(
    orders: List[Dict[str, Any]],
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Place multiple orders in a single batch request.

    Args:
        orders: List of order dictionaries, each containing:
            - coin: str
            - is_buy: bool
            - size: float
            - price: float
            - order_type: str (optional)
            - tif: str (optional)
            - reduce_only: bool (optional)
            - cloid: str (optional)

    Returns:
        List of result dictionaries, one per order
    """
    # Use global app_context
    if ctx: ctx.info(f"Placing batch of {len(orders)} orders")

    result = await app_context.trading_tools.place_batch_orders(orders)
    return result


@mcp.tool()
async def cancel_order(
    coin: str,
    order_id: Optional[int] = None,
    cloid: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Cancel a specific order by order ID or client order ID.

    Args:
        coin: Trading pair symbol
        order_id: Exchange order ID (optional if cloid provided)
        cloid: Client order ID (optional if order_id provided)

    Returns:
        Cancellation result with status
    """
    # Use global app_context
    if ctx: ctx.info(f"Canceling order for {coin}: order_id={order_id}, cloid={cloid}")

    result = await app_context.trading_tools.cancel_order(
        coin=coin,
        order_id=order_id,
        cloid=cloid
    )
    return result


@mcp.tool()
async def cancel_all_orders(
    coin: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Cancel all open orders, optionally filtered by coin.

    Args:
        coin: Trading pair symbol (if None, cancels ALL orders across all coins)

    Returns:
        Cancellation results including count of canceled orders

    Warning:
        If coin is None, this will cancel ALL open orders on the account.
    """
    # Use global app_context
    if ctx: ctx.info(f"Canceling all orders{f' for {coin}' if coin else ' across all coins'}")

    result = await app_context.trading_tools.cancel_all_orders(coin)
    return result


@mcp.tool()
async def modify_order(
    coin: str,
    order_id: int,
    new_price: Optional[float] = None,
    new_size: Optional[float] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Modify an existing order's price and/or size.

    Args:
        coin: Trading pair symbol
        order_id: Exchange order ID to modify
        new_price: New limit price (optional)
        new_size: New order size (optional)

    Returns:
        Modification result with updated order details

    Note:
        On Hyperliquid, modifying an order may result in a new order ID.
    """
    # Use global app_context
    if ctx: ctx.info(f"Modifying order {order_id} for {coin}: price={new_price}, size={new_size}")

    result = await app_context.trading_tools.modify_order(
        coin=coin,
        order_id=order_id,
        new_price=new_price,
        new_size=new_size
    )
    return result


@mcp.tool()
async def place_twap_order(
    coin: str,
    is_buy: bool,
    total_size: float,
    duration_minutes: int,
    randomize: bool = False,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Place a Time-Weighted Average Price (TWAP) order.

    TWAP orders split a large order into smaller chunks executed over time
    to minimize market impact and achieve better average execution price.

    Args:
        coin: Trading pair symbol
        is_buy: True for buy, False for sell
        total_size: Total size to execute over the duration
        duration_minutes: Time period to spread the order over (in minutes)
        randomize: If True, randomize slice timing to reduce predictability

    Returns:
        TWAP order details including estimated slices and timing
    """
    # Use global app_context
    if ctx: ctx.info(f"Placing TWAP order: {total_size} {coin} over {duration_minutes}m")

    result = await app_context.trading_tools.place_twap_order(
        coin=coin,
        is_buy=is_buy,
        total_size=total_size,
        duration_minutes=duration_minutes,
        randomize=randomize
    )
    return result


@mcp.tool()
async def adjust_leverage(
    coin: str,
    leverage: int,
    is_cross: bool = True,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Adjust leverage for a perpetual trading pair.

    Args:
        coin: Trading pair symbol
        leverage: Leverage multiplier (e.g., 10 for 10x)
        is_cross: True for cross margin, False for isolated margin

    Returns:
        Leverage adjustment result

    Warning:
        Higher leverage increases both potential profits and losses.
        Maximum leverage varies by asset (typically 20-50x).
    """
    # Use global app_context
    if ctx: ctx.info(f"Adjusting leverage for {coin} to {leverage}x ({'cross' if is_cross else 'isolated'})")

    result = await app_context.trading_tools.adjust_leverage(
        coin=coin,
        leverage=leverage,
        is_cross=is_cross
    )
    return result


@mcp.tool()
async def modify_isolated_margin(
    coin: str,
    amount: float,
    is_add: bool = True,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Add or remove USDC from an isolated margin position.

    Args:
        coin: Trading pair symbol
        amount: Amount of USDC to add or remove
        is_add: True to add margin, False to remove margin

    Returns:
        Margin modification result

    Note:
        This only works for positions in isolated margin mode.

    Warning:
        Removing too much margin may trigger liquidation.
    """
    # Use global app_context
    if ctx: ctx.info(f"{'Adding' if is_add else 'Removing'} {amount} USDC margin for {coin}")

    result = await app_context.trading_tools.modify_isolated_margin(
        coin=coin,
        amount=amount,
        is_add=is_add
    )
    return result


@mcp.tool()
async def update_dead_mans_switch(
    delay_seconds: int,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Configure dead man's switch to auto-cancel all orders after a delay.

    The dead man's switch is a safety mechanism that automatically cancels
    all open orders if not refreshed within the specified delay.

    Args:
        delay_seconds: Time in seconds before auto-canceling (minimum 5)

    Returns:
        Dead man's switch configuration result

    Warning:
        If the delay expires, ALL open orders will be canceled immediately.
    """
    # Use global app_context
    if ctx: ctx.info(f"Updating dead man's switch: {delay_seconds}s delay")

    result = await app_context.trading_tools.update_dead_mans_switch(delay_seconds)
    return result


# ============================================================================
# ACCOUNT TOOLS (8 methods)
# ============================================================================

@mcp.tool()
async def get_user_state(
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get complete account state including balances, positions, and margin info.

    Returns:
        Account state data including:
        - account_value: Total account value in USD
        - total_margin_used: Margin currently in use
        - withdrawable: Available balance to withdraw
        - balances: List of asset balances
        - positions: Open positions
        - margin_summary: Margin utilization details
    """
    # Use global app_context
    if ctx: ctx.info(f"Fetching user state for account {app_context.account_address[:8]}...")

    result = await app_context.account_tools.get_user_state()
    return result


@mcp.tool()
async def get_open_orders(
    coin: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get all open orders, optionally filtered by coin.

    Args:
        coin: Optional coin symbol to filter orders (e.g., "BTC", "ETH")

    Returns:
        List of open orders with details including order ID, size, price, side
    """
    # Use global app_context
    if ctx: ctx.info(f"Fetching open orders{f' for {coin}' if coin else ''}")

    result = await app_context.account_tools.get_open_orders(coin)
    return result


@mcp.tool()
async def get_positions(
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get all open positions with detailed metrics.

    Returns:
        List of open positions with:
        - coin, size, entry_price, unrealized_pnl
        - leverage, margin_used, position_value
        - ROE percentage, liquidation price
    """
    # Use global app_context
    if ctx: ctx.info("Fetching open positions")

    result = await app_context.account_tools.get_positions()
    return result


@mcp.tool()
async def get_user_fills(
    coin: Optional[str] = None,
    limit: int = 100,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get recent trade fills, optionally filtered by coin.

    Args:
        coin: Optional coin symbol to filter fills
        limit: Maximum number of fills to return (max 2000)

    Returns:
        List of fills with trade details including price, size, fees, PnL
    """
    # Use global app_context
    if ctx: ctx.info(f"Fetching user fills{f' for {coin}' if coin else ''} (limit={limit})")

    result = await app_context.account_tools.get_user_fills(coin, limit)
    return result


@mcp.tool()
async def get_historical_orders(
    coin: Optional[str] = None,
    limit: int = 100,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get historical orders with their status.

    Args:
        coin: Optional coin symbol to filter orders
        limit: Maximum number of orders to return

    Returns:
        List of historical orders with status (filled, open, partially_filled)
    """
    # Use global app_context
    if ctx: ctx.info(f"Fetching historical orders{f' for {coin}' if coin else ''} (limit={limit})")

    result = await app_context.account_tools.get_historical_orders(coin, limit)
    return result


@mcp.tool()
async def get_portfolio_value(
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get comprehensive portfolio value and PnL analysis.

    Returns:
        Portfolio analytics including:
        - total_value, margin_used, available_margin
        - total_pnl, realized_pnl, unrealized_pnl
        - pnl_percentage, total_fees_paid
        - breakdown by coin with position allocation
    """
    # Use global app_context
    if ctx: ctx.info("Calculating portfolio value and PnL")

    result = await app_context.account_tools.get_portfolio_value()
    return result


@mcp.tool()
async def get_subaccounts(
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get list of subaccounts and their states.

    Returns:
        List of subaccounts with account values and positions
    """
    # Use global app_context
    if ctx: ctx.info("Fetching subaccounts")

    result = await app_context.account_tools.get_subaccounts()
    return result


@mcp.tool()
async def get_rate_limit_status(
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get current rate limit usage and status.

    Returns:
        Rate limit information including:
        - requests_used, requests_limit, requests_remaining
        - weight_used, weight_limit, weight_remaining
        - reset_time, status (healthy/warning/critical)
        - recommendations for rate limit management
    """
    # Use global app_context
    if ctx: ctx.info("Checking rate limit status")

    result = await app_context.account_tools.get_rate_limit_status()
    return result


# ============================================================================
# MARKET TOOLS (6 methods)
# ============================================================================

@mcp.tool()
async def get_all_mids(
    ctx: Context = None
) -> Dict[str, float]:
    """
    Get mid prices for all available coins.

    Returns:
        Dictionary mapping coin symbols to their mid prices
        Example: {"BTC": 45000.0, "ETH": 2500.0, "SOL": 100.5}
    """
    # Use global app_context
    if ctx: ctx.info("Fetching all mid prices")

    # Note: This is NOT async in the tool class
    result = app_context.market_tools.get_all_mids()
    return result


@mcp.tool()
async def get_l2_orderbook(
    coin: str,
    depth: int = 20,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get Level 2 order book snapshot for a coin.

    Args:
        coin: Symbol to get order book for (e.g., "BTC", "ETH")
        depth: Number of price levels per side (max 20)

    Returns:
        Order book with bids, asks, spread, volumes, and liquidity metrics
    """
    # Use global app_context
    if ctx: ctx.info(f"Fetching L2 orderbook for {coin} (depth={depth})")

    # Note: This is NOT async in the tool class
    result = app_context.market_tools.get_l2_orderbook(coin, depth)
    return result


@mcp.tool()
async def get_candles(
    coin: str,
    interval: str = "1h",
    limit: int = 100,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Get historical candle (OHLCV) data.

    Args:
        coin: Symbol to get candles for (e.g., "BTC", "ETH")
        interval: Candle interval - "1m", "5m", "15m", "1h", "4h", "1d"
        limit: Number of candles to return (max 5000)

    Returns:
        List of candles with timestamp, open, high, low, close, volume
    """
    # Use global app_context
    if ctx: ctx.info(f"Fetching {limit} {interval} candles for {coin}")

    # Note: This is NOT async in the tool class
    result = app_context.market_tools.get_candles(coin, interval, limit)
    return result


@mcp.tool()
async def get_recent_trades(
    coin: str,
    limit: int = 50,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Get recent trades for a coin.

    Args:
        coin: Symbol to get trades for (e.g., "BTC", "ETH")
        limit: Number of recent trades to return

    Returns:
        List of trades sorted by most recent first with price, size, side, timestamp
    """
    # Use global app_context
    if ctx: ctx.info(f"Fetching {limit} recent trades for {coin}")

    # Note: This is NOT async in the tool class
    result = app_context.market_tools.get_recent_trades(coin, limit)
    return result


@mcp.tool()
async def get_funding_rates(
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Get current funding rates for all perpetual contracts.

    Returns:
        List of funding rates with:
        - coin: Symbol
        - funding_rate: Current funding rate (annualized %)
        - next_funding_time: Next funding payment time
        - mark_price, index_price, premium
    """
    # Use global app_context
    if ctx: ctx.info("Fetching funding rates for all perpetuals")

    # Note: This is NOT async in the tool class
    result = app_context.market_tools.get_funding_rates()
    return result


@mcp.tool()
async def get_asset_contexts(
    coin: str,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get comprehensive asset context and market conditions.

    Args:
        coin: Symbol to get context for (e.g., "BTC", "ETH")

    Returns:
        Asset context including:
        - mark_price, oracle_price, index_price
        - funding_rate, open_interest, open_interest_usd
        - volume_24h, trades_24h
    """
    # Use global app_context
    if ctx: ctx.info(f"Fetching asset contexts for {coin}")

    # Note: This is NOT async in the tool class
    result = app_context.market_tools.get_asset_contexts(coin)
    return result


# ============================================================================
# WEBSOCKET TOOLS (4 methods)
# ============================================================================

@mcp.tool()
async def subscribe_user_events(
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Subscribe to user events (fills, funding, liquidations).

    Returns:
        Subscription details including subscription ID and status

    Note:
        Requires WebSocket connection to be established first.
    """
    # Use global app_context
    if ctx: ctx.info(f"Subscribing to user events for {app_context.account_address[:8]}...")

    try:
        # Ensure WebSocket is started
        if not app_context.websocket_tools.manager.connected:
            await app_context.websocket_tools.start()

        subscription_id = await app_context.websocket_tools.subscribe_user_events()

        return {
            "success": True,
            "subscription_id": subscription_id,
            "subscription_type": "user_events",
            "account": app_context.account_address
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def subscribe_market_data(
    coin: str,
    data_types: List[str],
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Subscribe to market data streams.

    Args:
        coin: Symbol to subscribe to (e.g., "BTC", "ETH")
        data_types: List of data types - "l2Book", "trades", "candle"

    Returns:
        Subscription details including list of subscription IDs

    Note:
        Requires WebSocket connection to be established first.
    """
    # Use global app_context
    if ctx: ctx.info(f"Subscribing to market data for {coin}: {data_types}")

    try:
        # Ensure WebSocket is started
        if not app_context.websocket_tools.manager.connected:
            await app_context.websocket_tools.start()

        subscription_ids = await app_context.websocket_tools.subscribe_market_data(
            coin=coin,
            data_types=data_types
        )

        return {
            "success": True,
            "subscription_ids": subscription_ids,
            "coin": coin,
            "data_types": data_types
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def subscribe_order_updates(
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Subscribe to order updates and user fills.

    Returns:
        Subscription details including list of subscription IDs

    Note:
        Requires WebSocket connection to be established first.
        Subscribes to both orderUpdates and userFills channels.
    """
    # Use global app_context
    if ctx: ctx.info(f"Subscribing to order updates for {app_context.account_address[:8]}...")

    try:
        # Ensure WebSocket is started
        if not app_context.websocket_tools.manager.connected:
            await app_context.websocket_tools.start()

        subscription_ids = await app_context.websocket_tools.subscribe_order_updates()

        return {
            "success": True,
            "subscription_ids": subscription_ids,
            "subscription_types": ["order_updates", "user_fills"],
            "account": app_context.account_address
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def get_active_subscriptions(
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get list of all active WebSocket subscriptions.

    Returns:
        List of active subscriptions with:
        - subscription_id: Unique subscription identifier
        - subscription_type: Type of subscription
        - params: Subscription parameters
        - connected: Connection status
        - messages_received: Number of messages received
        - subscribed_at: Subscription timestamp
    """
    # Use global app_context
    if ctx: ctx.info("Fetching active WebSocket subscriptions")

    try:
        subscriptions = app_context.websocket_tools.get_active_subscriptions()
        connection_stats = app_context.websocket_tools.get_connection_stats()

        return {
            "success": True,
            "subscriptions": subscriptions,
            "connection_stats": connection_stats,
            "total_subscriptions": len(subscriptions)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("config://hyperliquid")
def get_hyperliquid_config() -> str:
    """Get current Hyperliquid configuration and connection status."""
    return get_config_summary()


@mcp.resource("guide://trading")
def get_trading_guide() -> str:
    """Guide for trading on Hyperliquid."""
    return """Hyperliquid Trading Guide:

## Order Types:
- Market Order: Execute immediately at current market price
- Limit Order: Execute at specific price or better
- Reduce-Only: Only reduce existing position size

## Position Management:
- Long positions: Profit when price increases
- Short positions: Profit when price decreases
- Use stop-loss orders to manage risk
- Monitor margin usage to avoid liquidation

## Risk Management:
- Never risk more than you can afford to lose
- Use appropriate position sizing
- Set stop-loss levels before entering trades
- Monitor funding rates for perpetual contracts
- Keep sufficient margin for volatile markets

## Best Practices:
1. Start with small position sizes
2. Use limit orders to control execution price
3. Monitor liquidation price on leveraged positions
4. Keep track of funding rate costs
5. Use the account state tool to monitor overall exposure
"""


@mcp.resource("guide://symbols")
def get_symbols_guide() -> str:
    """Guide to available trading symbols on Hyperliquid."""
    return """Hyperliquid Trading Symbols:

## Major Cryptocurrencies:
- BTC - Bitcoin
- ETH - Ethereum
- SOL - Solana
- AVAX - Avalanche
- MATIC - Polygon

## Order Size Guidelines:
- Check minimum order size for each symbol
- Use appropriate decimal precision
- Consider liquidity before placing large orders

## Price Precision:
- Different symbols have different tick sizes
- Limit prices must match the tick size
- Use market data tools to check current precision

## Trading Hours:
- Hyperliquid operates 24/7
- No trading halts or market closures
- Funding occurs every 8 hours for perpetuals

## Liquidity Considerations:
- Check order book depth before large trades
- Use limit orders for better execution
- Consider market impact on large positions
"""


# ============================================================================
# SERVER EXECUTION
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting Hyperliquid MCP Server with stdio transport...")
    mcp.run(transport='stdio')
