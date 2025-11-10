"""
Hyperliquid Market Data Tools

Provides comprehensive market data access including:
- Real-time price feeds
- Order book data (L2)
- Historical candles (OHLCV)
- Recent trades
- Funding rates
- Asset contexts and open interest
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MarketTools:
    """
    Tools for retrieving market data from Hyperliquid.

    This class provides methods for:
    - Getting real-time prices and order book data
    - Retrieving historical OHLCV candles
    - Viewing market statistics and funding rates
    - Analyzing trading volume and liquidity
    """

    def __init__(self, info_client, account_address: Optional[str] = None):
        """
        Initialize market data tools.

        Args:
            info_client: Hyperliquid Info client for reading market data
            account_address: Optional account address for personalized data
        """
        self.info = info_client
        self.account_address = account_address
        self.logger = logging.getLogger(__name__)

        self.logger.info("MarketTools initialized")

    def get_all_mids(self) -> Dict[str, float]:
        """
        Get mid prices for all available coins

        Returns:
            Dictionary mapping coin symbols to their mid prices
            Example: {"BTC": 45000.0, "ETH": 2500.0, "SOL": 100.5}

        Raises:
            Exception: If API call fails
        """
        try:
            self.logger.debug("Fetching all mid prices")
            mids = self.info.all_mids()

            if not mids:
                self.logger.warning("No mid prices returned from API")
                return {}

            # Convert to float and format
            result = {
                coin: float(price)
                for coin, price in mids.items()
            }

            self.logger.info(f"Retrieved {len(result)} mid prices")
            return result

        except Exception as e:
            self.logger.error(f"Error fetching mid prices: {e}")
            raise Exception(f"Failed to get mid prices: {str(e)}")

    def get_l2_orderbook(
        self,
        coin: str,
        depth: int = 20
    ) -> Dict[str, Any]:
        """
        Get Level 2 order book snapshot for a coin

        Args:
            coin: Symbol to get order book for (e.g., "BTC", "ETH")
            depth: Number of price levels per side (max 20)

        Returns:
            Dictionary containing:
            - bids: List of [price, size] arrays
            - asks: List of [price, size] arrays
            - spread: Difference between best ask and best bid
            - mid_price: Average of best bid and ask
            - bid_volume: Total volume on bid side
            - ask_volume: Total volume on ask side
            - timestamp: Snapshot timestamp

        Raises:
            ValueError: If depth is invalid
            Exception: If API call fails
        """
        if depth <= 0 or depth > 20:
            raise ValueError("Depth must be between 1 and 20")

        try:
            self.logger.debug(f"Fetching L2 orderbook for {coin} with depth {depth}")
            snapshot = self.info.l2_snapshot(coin)

            if not snapshot:
                raise Exception(f"No orderbook data returned for {coin}")

            # Extract and limit depth
            bids = snapshot.get("levels", [[[], []]])[0][:depth]
            asks = snapshot.get("levels", [[[], []]])[1][:depth]

            # Calculate metrics
            best_bid = float(bids[0][0]) if bids else 0.0
            best_ask = float(asks[0][0]) if asks else 0.0

            spread = best_ask - best_bid if best_bid and best_ask else 0.0
            mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else 0.0

            # Calculate total volumes
            bid_volume = sum(float(level[1]) for level in bids)
            ask_volume = sum(float(level[1]) for level in asks)

            result = {
                "coin": coin,
                "bids": [[float(price), float(size)] for price, size in bids],
                "asks": [[float(price), float(size)] for price, size in asks],
                "spread": spread,
                "spread_bps": (spread / mid_price * 10000) if mid_price else 0.0,
                "mid_price": mid_price,
                "best_bid": best_bid,
                "best_ask": best_ask,
                "bid_volume": bid_volume,
                "ask_volume": ask_volume,
                "total_volume": bid_volume + ask_volume,
                "timestamp": snapshot.get("time", datetime.now().isoformat()),
                "depth": len(bids)
            }

            self.logger.info(f"Retrieved L2 orderbook for {coin}: mid={mid_price}, spread={spread:.4f}")
            return result

        except Exception as e:
            self.logger.error(f"Error fetching L2 orderbook for {coin}: {e}")
            raise Exception(f"Failed to get orderbook for {coin}: {str(e)}")

    def get_candles(
        self,
        coin: str,
        interval: str = "1h",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get historical candle (OHLCV) data

        Args:
            coin: Symbol to get candles for (e.g., "BTC", "ETH")
            interval: Candle interval - "1m", "5m", "15m", "1h", "4h", "1d"
            limit: Number of candles to return (max 5000)

        Returns:
            List of candle dictionaries with:
            - timestamp: Candle open time (ISO format)
            - time_ms: Candle open time (milliseconds)
            - open: Open price
            - high: High price
            - low: Low price
            - close: Close price
            - volume: Trading volume
            - num_trades: Number of trades (if available)

        Raises:
            ValueError: If interval is invalid
            Exception: If API call fails
        """
        valid_intervals = ["1m", "5m", "15m", "1h", "4h", "1d"]
        if interval not in valid_intervals:
            raise ValueError(f"Invalid interval. Must be one of: {valid_intervals}")

        if limit <= 0 or limit > 5000:
            raise ValueError("Limit must be between 1 and 5000")

        try:
            self.logger.debug(f"Fetching {limit} candles for {coin} at {interval} interval")
            candles = self.info.candles_snapshot(coin, interval, limit)

            if not candles:
                self.logger.warning(f"No candle data returned for {coin}")
                return []

            result = []
            for candle in candles:
                # Parse candle data
                candle_dict = {
                    "timestamp": datetime.fromtimestamp(candle["t"] / 1000).isoformat(),
                    "time_ms": candle["t"],
                    "open": float(candle["o"]),
                    "high": float(candle["h"]),
                    "low": float(candle["l"]),
                    "close": float(candle["c"]),
                    "volume": float(candle["v"]),
                }

                # Add number of trades if available
                if "n" in candle:
                    candle_dict["num_trades"] = candle["n"]

                result.append(candle_dict)

            self.logger.info(f"Retrieved {len(result)} candles for {coin}")
            return result

        except Exception as e:
            self.logger.error(f"Error fetching candles for {coin}: {e}")
            raise Exception(f"Failed to get candles for {coin}: {str(e)}")

    def get_recent_trades(
        self,
        coin: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent trades for a coin

        Args:
            coin: Symbol to get trades for (e.g., "BTC", "ETH")
            limit: Number of recent trades to return

        Returns:
            List of trade dictionaries sorted by most recent first:
            - timestamp: Trade execution time (ISO format)
            - time_ms: Trade execution time (milliseconds)
            - price: Trade price
            - size: Trade size
            - side: Trade side ("buy" or "sell")
            - trade_id: Unique trade identifier (if available)

        Raises:
            Exception: If API call fails
        """
        if limit <= 0:
            raise ValueError("Limit must be positive")

        try:
            self.logger.debug(f"Fetching {limit} recent trades for {coin}")
            trades = self.info.recent_trades(coin)

            if not trades:
                self.logger.warning(f"No trade data returned for {coin}")
                return []

            # Sort by timestamp descending (most recent first)
            sorted_trades = sorted(
                trades,
                key=lambda x: x.get("time", 0),
                reverse=True
            )[:limit]

            result = []
            for trade in sorted_trades:
                trade_dict = {
                    "timestamp": datetime.fromtimestamp(trade["time"] / 1000).isoformat(),
                    "time_ms": trade["time"],
                    "price": float(trade["px"]),
                    "size": float(trade["sz"]),
                    "side": trade["side"].lower(),
                }

                # Add trade ID if available
                if "tid" in trade:
                    trade_dict["trade_id"] = trade["tid"]

                result.append(trade_dict)

            self.logger.info(f"Retrieved {len(result)} recent trades for {coin}")
            return result

        except Exception as e:
            self.logger.error(f"Error fetching recent trades for {coin}: {e}")
            raise Exception(f"Failed to get recent trades for {coin}: {str(e)}")

    def get_funding_rates(self) -> List[Dict[str, Any]]:
        """
        Get current funding rates for all perpetual contracts

        Returns:
            List of funding rate dictionaries:
            - coin: Symbol
            - funding_rate: Current funding rate (annualized %)
            - next_funding_time: Next funding payment time (ISO format)
            - predicted_rate: Predicted funding rate (if available)
            - premium: Index-mark price premium
            - mark_price: Current mark price
            - index_price: Current index price

        Raises:
            Exception: If API call fails
        """
        try:
            self.logger.debug("Fetching funding rates for all perpetuals")
            meta = self.info.meta()

            if not meta or "universe" not in meta:
                raise Exception("No metadata returned from API")

            result = []
            for asset in meta["universe"]:
                if asset.get("name"):
                    funding_info = {
                        "coin": asset["name"],
                        "funding_rate": float(asset.get("funding", 0)) * 100,  # Convert to %
                    }

                    # Add next funding time if available
                    if "nextFundingTime" in asset:
                        funding_info["next_funding_time"] = datetime.fromtimestamp(
                            asset["nextFundingTime"] / 1000
                        ).isoformat()

                    # Add predicted rate if available
                    if "predictedFunding" in asset:
                        funding_info["predicted_rate"] = float(asset["predictedFunding"]) * 100

                    # Add premium if available
                    if "premium" in asset:
                        funding_info["premium"] = float(asset["premium"])

                    # Add prices if available
                    if "markPx" in asset:
                        funding_info["mark_price"] = float(asset["markPx"])

                    if "indexPx" in asset:
                        funding_info["index_price"] = float(asset["indexPx"])

                    result.append(funding_info)

            self.logger.info(f"Retrieved funding rates for {len(result)} perpetuals")
            return result

        except Exception as e:
            self.logger.error(f"Error fetching funding rates: {e}")
            raise Exception(f"Failed to get funding rates: {str(e)}")

    def get_asset_contexts(self, coin: str) -> Dict[str, Any]:
        """
        Get comprehensive asset context and market conditions

        Args:
            coin: Symbol to get context for (e.g., "BTC", "ETH")

        Returns:
            Dictionary containing:
            - coin: Symbol
            - mark_price: Current mark price
            - oracle_price: Oracle price
            - index_price: Index price
            - funding_rate: Current funding rate (%)
            - open_interest: Total open interest
            - open_interest_usd: Open interest in USD
            - funding: Raw funding value
            - prevailing_px: Prevailing market price
            - volume_24h: 24h trading volume (if available)
            - trades_24h: 24h number of trades (if available)

        Raises:
            Exception: If API call fails or coin not found
        """
        try:
            self.logger.debug(f"Fetching asset contexts for {coin}")
            data = self.info.meta_and_asset_ctxs()

            if not data:
                raise Exception("No data returned from API")

            # Find the specific coin in universe
            meta = data[0]  # Metadata
            asset_ctxs = data[1]  # Asset contexts

            coin_meta = None
            coin_ctx = None

            # Find coin in metadata
            for idx, asset in enumerate(meta.get("universe", [])):
                if asset.get("name") == coin:
                    coin_meta = asset
                    if idx < len(asset_ctxs):
                        coin_ctx = asset_ctxs[idx]
                    break

            if not coin_meta:
                raise Exception(f"Coin {coin} not found in market data")

            result = {
                "coin": coin,
                "mark_price": float(coin_ctx.get("markPx", 0)) if coin_ctx else 0.0,
                "oracle_price": float(coin_ctx.get("oraclePx", 0)) if coin_ctx else 0.0,
                "funding_rate": float(coin_meta.get("funding", 0)) * 100,
                "open_interest": float(coin_ctx.get("openInterest", 0)) if coin_ctx else 0.0,
            }

            # Calculate OI in USD
            if result["mark_price"] and result["open_interest"]:
                result["open_interest_usd"] = result["mark_price"] * result["open_interest"]
            else:
                result["open_interest_usd"] = 0.0

            # Add index price if available
            if coin_meta.get("indexPx"):
                result["index_price"] = float(coin_meta["indexPx"])

            # Add prevailing price if available
            if coin_ctx and "prevailPx" in coin_ctx:
                result["prevailing_px"] = float(coin_ctx["prevailPx"])

            # Add funding details
            if coin_ctx and "funding" in coin_ctx:
                result["funding"] = float(coin_ctx["funding"])

            # Add 24h volume and trades if available
            if coin_ctx:
                if "dayNtlVlm" in coin_ctx:
                    result["volume_24h"] = float(coin_ctx["dayNtlVlm"])

                if "dayNtlTrades" in coin_ctx:
                    result["trades_24h"] = int(coin_ctx["dayNtlTrades"])

            self.logger.info(f"Retrieved asset context for {coin}")
            return result

        except Exception as e:
            self.logger.error(f"Error fetching asset contexts for {coin}: {e}")
            raise Exception(f"Failed to get asset contexts for {coin}: {str(e)}")
