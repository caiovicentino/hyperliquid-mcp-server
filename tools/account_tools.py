"""
Account Management Tools for Hyperliquid MCP Server

This module provides comprehensive account querying capabilities including:
- Account state and balances
- Open orders and positions
- Trade history and fills
- Portfolio analytics
- Rate limit monitoring
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class AccountTools:
    """
    Account management and query tools for Hyperliquid trading accounts.

    Provides methods to retrieve account state, positions, orders, fills,
    and portfolio analytics with proper error handling and formatting.
    """

    def __init__(self, info_client, account_address: str):
        """
        Initialize AccountTools with Hyperliquid Info client.

        Args:
            info_client: Hyperliquid Info API client instance
            account_address: Ethereum address of the account to query
        """
        self.info = info_client
        self.account = account_address

    def _format_timestamp(self, timestamp_ms: int) -> str:
        """
        Convert millisecond timestamp to human-readable format.

        Args:
            timestamp_ms: Unix timestamp in milliseconds

        Returns:
            ISO 8601 formatted datetime string
        """
        try:
            dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            return dt.isoformat()
        except Exception as e:
            logger.warning(f"Failed to format timestamp {timestamp_ms}: {e}")
            return str(timestamp_ms)

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """
        Safely convert value to float.

        Args:
            value: Value to convert
            default: Default value if conversion fails

        Returns:
            Float value or default
        """
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    async def get_user_state(self) -> Dict[str, Any]:
        """
        Get complete account state including balances, positions, and margin info.

        Returns:
            Dict containing:
                - success: Boolean indicating success
                - data: Account state data including:
                    - account_value: Total account value in USD
                    - total_margin_used: Margin currently in use
                    - withdrawable: Available balance to withdraw
                    - balances: List of asset balances
                    - positions: Open positions
                    - margin_summary: Margin utilization details
                - error: Error message if failed
        """
        try:
            user_state = self.info.user_state(self.account)

            if not user_state:
                return {
                    "success": False,
                    "data": None,
                    "error": "No user state data returned"
                }

            # Extract margin summary
            margin_summary = user_state.get("marginSummary", {})
            account_value = self._safe_float(margin_summary.get("accountValue"))
            total_margin_used = self._safe_float(margin_summary.get("totalMarginUsed"))
            withdrawable = self._safe_float(user_state.get("withdrawable"))

            # Parse asset positions (balances)
            asset_positions = []
            for asset in user_state.get("assetPositions", []):
                position_data = asset.get("position", {})
                asset_positions.append({
                    "coin": position_data.get("coin", "Unknown"),
                    "entry_price": self._safe_float(position_data.get("entryPx")),
                    "position_value": self._safe_float(position_data.get("positionValue")),
                    "unrealized_pnl": self._safe_float(position_data.get("unrealizedPnl")),
                    "return_on_equity": self._safe_float(position_data.get("returnOnEquity")),
                })

            # Extract cross margin summary
            cross_margin = user_state.get("crossMarginSummary", {})

            formatted_data = {
                "account_value": account_value,
                "total_margin_used": total_margin_used,
                "withdrawable": withdrawable,
                "available_margin": account_value - total_margin_used,
                "margin_utilization_pct": (total_margin_used / account_value * 100) if account_value > 0 else 0,
                "balances": asset_positions,
                "positions_count": len(asset_positions),
                "margin_summary": {
                    "total_raw_usd": self._safe_float(margin_summary.get("totalRawUsd")),
                    "total_ntl_pos": self._safe_float(margin_summary.get("totalNtlPos")),
                    "cross_maintenance_margin": self._safe_float(cross_margin.get("crossMaintenanceMarginUsed"))
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            return {
                "success": True,
                "data": formatted_data,
                "error": None
            }

        except Exception as e:
            logger.error(f"Error getting user state for {self.account}: {e}")
            return {
                "success": False,
                "data": None,
                "error": f"Failed to get user state: {str(e)}"
            }

    async def get_open_orders(self, coin: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all open orders, optionally filtered by coin.

        Args:
            coin: Optional coin symbol to filter orders (e.g., "BTC", "ETH")

        Returns:
            Dict containing:
                - success: Boolean indicating success
                - data: List of open orders with details
                - error: Error message if failed
        """
        try:
            open_orders = self.info.open_orders(self.account)

            if not open_orders:
                return {
                    "success": True,
                    "data": {
                        "orders": [],
                        "total_count": 0,
                        "filtered_by_coin": coin
                    },
                    "error": None
                }

            formatted_orders = []
            for order in open_orders:
                order_coin = order.get("coin", "")

                # Filter by coin if specified
                if coin and order_coin.upper() != coin.upper():
                    continue

                formatted_orders.append({
                    "order_id": order.get("oid"),
                    "coin": order_coin,
                    "side": order.get("side"),
                    "size": self._safe_float(order.get("sz")),
                    "price": self._safe_float(order.get("limitPx")),
                    "filled_size": self._safe_float(order.get("szFilled", 0)),
                    "remaining_size": self._safe_float(order.get("sz")) - self._safe_float(order.get("szFilled", 0)),
                    "order_type": order.get("orderType", "limit"),
                    "reduce_only": order.get("reduceOnly", False),
                    "timestamp": self._format_timestamp(order.get("timestamp", 0)),
                    "original_size": self._safe_float(order.get("origSz"))
                })

            # Sort by timestamp (newest first)
            formatted_orders.sort(key=lambda x: x["timestamp"], reverse=True)

            return {
                "success": True,
                "data": {
                    "orders": formatted_orders,
                    "total_count": len(formatted_orders),
                    "filtered_by_coin": coin
                },
                "error": None
            }

        except Exception as e:
            logger.error(f"Error getting open orders for {self.account}: {e}")
            return {
                "success": False,
                "data": None,
                "error": f"Failed to get open orders: {str(e)}"
            }

    async def get_positions(self) -> Dict[str, Any]:
        """
        Get all open positions with detailed metrics.

        Returns:
            Dict containing:
                - success: Boolean indicating success
                - data: List of open positions with:
                    - coin, size, entry_price, unrealized_pnl
                    - leverage, margin_used, position_value
                    - ROE percentage
                - error: Error message if failed
        """
        try:
            user_state = self.info.user_state(self.account)

            if not user_state:
                return {
                    "success": False,
                    "data": None,
                    "error": "No user state data returned"
                }

            positions = []
            total_unrealized_pnl = 0.0
            total_position_value = 0.0

            for asset in user_state.get("assetPositions", []):
                position = asset.get("position", {})

                # Get position size
                size = self._safe_float(position.get("szi"))

                # Skip if no position
                if size == 0:
                    continue

                coin = position.get("coin", "Unknown")
                entry_price = self._safe_float(position.get("entryPx"))
                position_value = self._safe_float(position.get("positionValue"))
                unrealized_pnl = self._safe_float(position.get("unrealizedPnl"))
                leverage = self._safe_float(position.get("leverage", {}).get("value", 1))
                margin_used = self._safe_float(position.get("marginUsed"))
                roe = self._safe_float(position.get("returnOnEquity")) * 100  # Convert to percentage

                total_unrealized_pnl += unrealized_pnl
                total_position_value += abs(position_value)

                positions.append({
                    "coin": coin,
                    "side": "long" if size > 0 else "short",
                    "size": abs(size),
                    "entry_price": entry_price,
                    "position_value": position_value,
                    "unrealized_pnl": unrealized_pnl,
                    "leverage": leverage,
                    "margin_used": margin_used,
                    "roe_pct": roe,
                    "liquidation_price": self._safe_float(position.get("liquidationPx"))
                })

            return {
                "success": True,
                "data": {
                    "positions": positions,
                    "total_positions": len(positions),
                    "total_unrealized_pnl": total_unrealized_pnl,
                    "total_position_value": total_position_value,
                    "average_roe_pct": (total_unrealized_pnl / total_position_value * 100) if total_position_value > 0 else 0
                },
                "error": None
            }

        except Exception as e:
            logger.error(f"Error getting positions for {self.account}: {e}")
            return {
                "success": False,
                "data": None,
                "error": f"Failed to get positions: {str(e)}"
            }

    async def get_user_fills(self, coin: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """
        Get recent trade fills, optionally filtered by coin.

        Args:
            coin: Optional coin symbol to filter fills
            limit: Maximum number of fills to return (max 2000)

        Returns:
            Dict containing:
                - success: Boolean indicating success
                - data: List of fills with trade details
                - error: Error message if failed
        """
        try:
            # Ensure limit doesn't exceed API maximum
            limit = min(limit, 2000)

            user_fills = self.info.user_fills(self.account)

            if not user_fills:
                return {
                    "success": True,
                    "data": {
                        "fills": [],
                        "total_count": 0,
                        "filtered_by_coin": coin,
                        "limit": limit
                    },
                    "error": None
                }

            formatted_fills = []
            total_fees = 0.0
            total_volume = 0.0

            for fill in user_fills:
                fill_coin = fill.get("coin", "")

                # Filter by coin if specified
                if coin and fill_coin.upper() != coin.upper():
                    continue

                size = self._safe_float(fill.get("sz"))
                price = self._safe_float(fill.get("px"))
                fee = self._safe_float(fill.get("fee"))

                total_fees += fee
                total_volume += size * price

                formatted_fills.append({
                    "trade_id": fill.get("tid"),
                    "order_id": fill.get("oid"),
                    "coin": fill_coin,
                    "side": fill.get("side"),
                    "size": size,
                    "price": price,
                    "fee": fee,
                    "fee_token": fill.get("feeToken", "USDC"),
                    "closed_pnl": self._safe_float(fill.get("closedPnl")),
                    "timestamp": self._format_timestamp(fill.get("time", 0)),
                    "trade_value": size * price,
                    "start_position": self._safe_float(fill.get("startPosition"))
                })

                # Stop if we've reached the limit
                if len(formatted_fills) >= limit:
                    break

            # Sort by most recent first
            formatted_fills.sort(key=lambda x: x["timestamp"], reverse=True)

            return {
                "success": True,
                "data": {
                    "fills": formatted_fills,
                    "total_count": len(formatted_fills),
                    "total_fees": total_fees,
                    "total_volume": total_volume,
                    "filtered_by_coin": coin,
                    "limit": limit
                },
                "error": None
            }

        except Exception as e:
            logger.error(f"Error getting user fills for {self.account}: {e}")
            return {
                "success": False,
                "data": None,
                "error": f"Failed to get user fills: {str(e)}"
            }

    async def get_historical_orders(self, coin: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """
        Get historical orders with their status.

        Args:
            coin: Optional coin symbol to filter orders
            limit: Maximum number of orders to return

        Returns:
            Dict containing:
                - success: Boolean indicating success
                - data: List of historical orders
                - error: Error message if failed
        """
        try:
            # Note: Hyperliquid API may not have a direct historical_orders method
            # We'll use user_fills and open_orders to construct order history

            # Get open orders
            open_orders_result = await self.get_open_orders(coin)
            open_orders = open_orders_result.get("data", {}).get("orders", []) if open_orders_result.get("success") else []

            # Get fills to identify completed orders
            fills_result = await self.get_user_fills(coin, limit * 2)  # Get more fills to find unique orders
            fills = fills_result.get("data", {}).get("fills", []) if fills_result.get("success") else []

            # Build order history from fills
            orders_map = {}

            for fill in fills:
                oid = fill.get("order_id")
                if oid not in orders_map:
                    orders_map[oid] = {
                        "order_id": oid,
                        "coin": fill.get("coin"),
                        "side": fill.get("side"),
                        "total_filled_size": 0.0,
                        "average_price": 0.0,
                        "status": "filled",
                        "fills_count": 0,
                        "total_fees": 0.0,
                        "closed_pnl": 0.0,
                        "timestamp": fill.get("timestamp")
                    }

                orders_map[oid]["total_filled_size"] += fill.get("size", 0)
                orders_map[oid]["fills_count"] += 1
                orders_map[oid]["total_fees"] += fill.get("fee", 0)
                orders_map[oid]["closed_pnl"] += fill.get("closed_pnl", 0)

                # Update average price (weighted by size)
                current_total = orders_map[oid]["average_price"] * (orders_map[oid]["total_filled_size"] - fill.get("size", 0))
                new_total = current_total + (fill.get("price", 0) * fill.get("size", 0))
                orders_map[oid]["average_price"] = new_total / orders_map[oid]["total_filled_size"] if orders_map[oid]["total_filled_size"] > 0 else 0

            # Add open orders
            for order in open_orders:
                oid = order.get("order_id")
                if oid not in orders_map:
                    orders_map[oid] = {
                        "order_id": oid,
                        "coin": order.get("coin"),
                        "side": order.get("side"),
                        "size": order.get("size"),
                        "filled_size": order.get("filled_size"),
                        "remaining_size": order.get("remaining_size"),
                        "price": order.get("price"),
                        "status": "open",
                        "timestamp": order.get("timestamp")
                    }
                else:
                    # Order was partially filled and is still open
                    orders_map[oid]["status"] = "partially_filled"
                    orders_map[oid]["size"] = order.get("size")
                    orders_map[oid]["remaining_size"] = order.get("remaining_size")

            # Convert to list and sort by timestamp
            historical_orders = list(orders_map.values())
            historical_orders.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            # Apply limit
            historical_orders = historical_orders[:limit]

            # Calculate statistics
            filled_count = sum(1 for o in historical_orders if o["status"] == "filled")
            open_count = sum(1 for o in historical_orders if o["status"] == "open")
            partially_filled_count = sum(1 for o in historical_orders if o["status"] == "partially_filled")

            return {
                "success": True,
                "data": {
                    "orders": historical_orders,
                    "total_count": len(historical_orders),
                    "statistics": {
                        "filled": filled_count,
                        "open": open_count,
                        "partially_filled": partially_filled_count
                    },
                    "filtered_by_coin": coin,
                    "limit": limit
                },
                "error": None
            }

        except Exception as e:
            logger.error(f"Error getting historical orders for {self.account}: {e}")
            return {
                "success": False,
                "data": None,
                "error": f"Failed to get historical orders: {str(e)}"
            }

    async def get_portfolio_value(self) -> Dict[str, Any]:
        """
        Get comprehensive portfolio value and PnL analysis.

        Returns:
            Dict containing:
                - success: Boolean indicating success
                - data: Portfolio analytics including:
                    - total_value, margin_used, available_margin
                    - total_pnl, pnl_percentage
                    - breakdown by coin
                - error: Error message if failed
        """
        try:
            # Get user state for account value
            user_state_result = await self.get_user_state()
            if not user_state_result.get("success"):
                return user_state_result

            state_data = user_state_result.get("data", {})
            total_value = state_data.get("account_value", 0)
            margin_used = state_data.get("total_margin_used", 0)
            available_margin = state_data.get("available_margin", 0)

            # Get positions for unrealized PnL
            positions_result = await self.get_positions()
            positions_data = positions_result.get("data", {}) if positions_result.get("success") else {}
            unrealized_pnl = positions_data.get("total_unrealized_pnl", 0)

            # Get recent fills for realized PnL calculation
            fills_result = await self.get_user_fills(limit=500)
            fills_data = fills_result.get("data", {}) if fills_result.get("success") else {}
            fills = fills_data.get("fills", [])

            # Calculate realized PnL from fills
            realized_pnl = sum(fill.get("closed_pnl", 0) for fill in fills)
            total_fees = fills_data.get("total_fees", 0)

            # Calculate net PnL
            total_pnl = realized_pnl + unrealized_pnl

            # Calculate PnL percentage (based on initial investment)
            # Initial investment = current value - total PnL
            initial_investment = total_value - total_pnl
            pnl_percentage = (total_pnl / initial_investment * 100) if initial_investment > 0 else 0

            # Breakdown by coin
            coin_breakdown = []
            for position in positions_data.get("positions", []):
                coin_breakdown.append({
                    "coin": position.get("coin"),
                    "position_value": position.get("position_value"),
                    "unrealized_pnl": position.get("unrealized_pnl"),
                    "roe_pct": position.get("roe_pct"),
                    "percentage_of_portfolio": (abs(position.get("position_value", 0)) / total_value * 100) if total_value > 0 else 0
                })

            return {
                "success": True,
                "data": {
                    "total_value": total_value,
                    "margin_used": margin_used,
                    "available_margin": available_margin,
                    "margin_utilization_pct": (margin_used / total_value * 100) if total_value > 0 else 0,
                    "pnl": {
                        "total_pnl": total_pnl,
                        "realized_pnl": realized_pnl,
                        "unrealized_pnl": unrealized_pnl,
                        "pnl_percentage": pnl_percentage,
                        "total_fees_paid": total_fees,
                        "net_pnl": total_pnl - total_fees
                    },
                    "coin_breakdown": coin_breakdown,
                    "positions_count": len(coin_breakdown),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "error": None
            }

        except Exception as e:
            logger.error(f"Error getting portfolio value for {self.account}: {e}")
            return {
                "success": False,
                "data": None,
                "error": f"Failed to get portfolio value: {str(e)}"
            }

    async def get_subaccounts(self) -> Dict[str, Any]:
        """
        Get list of subaccounts and their states.

        Returns:
            Dict containing:
                - success: Boolean indicating success
                - data: List of subaccounts with states
                - error: Error message if failed
        """
        try:
            # Note: Check if Hyperliquid SDK has subaccounts method
            # This is a placeholder implementation

            # Try to get subaccounts info
            try:
                # Attempt to call subaccounts method if it exists
                subaccounts_data = self.info.subaccounts(self.account)

                if not subaccounts_data:
                    return {
                        "success": True,
                        "data": {
                            "subaccounts": [],
                            "total_count": 0,
                            "note": "No subaccounts found or feature not available"
                        },
                        "error": None
                    }

                formatted_subaccounts = []
                total_value = 0.0

                for subaccount in subaccounts_data:
                    account_value = self._safe_float(subaccount.get("accountValue"))
                    total_value += account_value

                    formatted_subaccounts.append({
                        "subaccount_address": subaccount.get("address"),
                        "account_value": account_value,
                        "positions_count": len(subaccount.get("positions", [])),
                        "margin_used": self._safe_float(subaccount.get("marginUsed")),
                        "withdrawable": self._safe_float(subaccount.get("withdrawable"))
                    })

                return {
                    "success": True,
                    "data": {
                        "subaccounts": formatted_subaccounts,
                        "total_count": len(formatted_subaccounts),
                        "total_value_all_subaccounts": total_value
                    },
                    "error": None
                }

            except AttributeError:
                # Subaccounts method doesn't exist
                return {
                    "success": True,
                    "data": {
                        "subaccounts": [],
                        "total_count": 0,
                        "note": "Subaccounts feature not available in current SDK version"
                    },
                    "error": None
                }

        except Exception as e:
            logger.error(f"Error getting subaccounts for {self.account}: {e}")
            return {
                "success": False,
                "data": None,
                "error": f"Failed to get subaccounts: {str(e)}"
            }

    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit usage and status.

        Returns:
            Dict containing:
                - success: Boolean indicating success
                - data: Rate limit information including:
                    - requests_used, requests_limit
                    - weight_used, weight_limit
                    - reset_time, percentage_used
                - error: Error message if failed
        """
        try:
            # Note: Check if Hyperliquid SDK has rate limit method
            # This may not be available in all SDK versions

            try:
                # Attempt to get rate limit info if available
                rate_limit_data = self.info.user_rate_limit(self.account)

                if not rate_limit_data:
                    # Return estimated rate limit info
                    return {
                        "success": True,
                        "data": {
                            "status": "unknown",
                            "note": "Rate limit data not available from API",
                            "estimated_limits": {
                                "requests_per_minute": 1200,
                                "weight_per_minute": 6000,
                                "note": "These are typical Hyperliquid limits, actual may vary"
                            }
                        },
                        "error": None
                    }

                requests_used = rate_limit_data.get("requestsUsed", 0)
                requests_limit = rate_limit_data.get("requestsLimit", 1200)
                weight_used = rate_limit_data.get("weightUsed", 0)
                weight_limit = rate_limit_data.get("weightLimit", 6000)
                reset_time_ms = rate_limit_data.get("resetTime", 0)

                # Calculate percentages
                requests_pct = (requests_used / requests_limit * 100) if requests_limit > 0 else 0
                weight_pct = (weight_used / weight_limit * 100) if weight_limit > 0 else 0

                # Calculate remaining capacity
                requests_remaining = requests_limit - requests_used
                weight_remaining = weight_limit - weight_used

                # Format reset time
                reset_time = self._format_timestamp(reset_time_ms)

                # Calculate seconds until reset
                now_ms = datetime.now(timezone.utc).timestamp() * 1000
                seconds_until_reset = max(0, (reset_time_ms - now_ms) / 1000)

                # Determine status
                if requests_pct > 90 or weight_pct > 90:
                    status = "critical"
                elif requests_pct > 70 or weight_pct > 70:
                    status = "warning"
                else:
                    status = "healthy"

                return {
                    "success": True,
                    "data": {
                        "status": status,
                        "requests": {
                            "used": requests_used,
                            "limit": requests_limit,
                            "remaining": requests_remaining,
                            "percentage_used": requests_pct
                        },
                        "weight": {
                            "used": weight_used,
                            "limit": weight_limit,
                            "remaining": weight_remaining,
                            "percentage_used": weight_pct
                        },
                        "reset_time": reset_time,
                        "seconds_until_reset": seconds_until_reset,
                        "recommendations": self._get_rate_limit_recommendations(requests_pct, weight_pct)
                    },
                    "error": None
                }

            except AttributeError:
                # Rate limit method doesn't exist
                return {
                    "success": True,
                    "data": {
                        "status": "unknown",
                        "note": "Rate limit monitoring not available in current SDK version",
                        "estimated_limits": {
                            "requests_per_minute": 1200,
                            "weight_per_minute": 6000,
                            "recommendation": "Monitor API response headers for rate limit info"
                        }
                    },
                    "error": None
                }

        except Exception as e:
            logger.error(f"Error getting rate limit status for {self.account}: {e}")
            return {
                "success": False,
                "data": None,
                "error": f"Failed to get rate limit status: {str(e)}"
            }

    def _get_rate_limit_recommendations(self, requests_pct: float, weight_pct: float) -> List[str]:
        """
        Get recommendations based on rate limit usage.

        Args:
            requests_pct: Percentage of requests used
            weight_pct: Percentage of weight used

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if requests_pct > 90 or weight_pct > 90:
            recommendations.append("CRITICAL: Rate limit near exhaustion. Pause non-essential requests.")
        elif requests_pct > 70 or weight_pct > 70:
            recommendations.append("WARNING: High rate limit usage. Consider reducing request frequency.")

        if requests_pct > 50:
            recommendations.append("Consider implementing request caching to reduce API calls.")

        if weight_pct > 50:
            recommendations.append("Heavy weight operations detected. Use batch requests where possible.")

        if not recommendations:
            recommendations.append("Rate limit usage is healthy. Continue normal operations.")

        return recommendations
