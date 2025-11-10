"""
Hyperliquid Trading Operations Module

This module provides a comprehensive set of trading tools for interacting with
the Hyperliquid DEX, including order placement, modification, cancellation,
leverage management, and advanced order types.

Author: Backend Developer
Date: 2025-11-09
"""

from typing import Dict, List, Optional, Any, Union
import time
from datetime import datetime, timedelta


class TradingTools:
    """
    TradingTools provides methods for executing trading operations on Hyperliquid.

    This class wraps the Hyperliquid SDK exchange and info clients to provide
    a clean, type-safe interface for trading operations including:
    - Single and batch order placement
    - Order cancellation and modification
    - TWAP (Time-Weighted Average Price) orders
    - Leverage and margin management
    - Dead man's switch for risk management
    """

    def __init__(self, exchange_client, info_client, account_address: str):
        """
        Initialize TradingTools with Hyperliquid SDK clients.

        Args:
            exchange_client: Hyperliquid Exchange client instance
            info_client: Hyperliquid Info client instance
            account_address: Ethereum address of the trading account
        """
        self.exchange = exchange_client
        self.info = info_client
        self.account = account_address

    async def place_order(
        self,
        coin: str,
        is_buy: bool,
        size: float,
        price: float,
        order_type: str = "limit",
        tif: str = "Gtc",
        reduce_only: bool = False,
        cloid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Place a single order on Hyperliquid.

        Args:
            coin: Trading pair symbol (e.g., "BTC", "ETH")
            is_buy: True for buy order, False for sell order
            size: Order size in base currency units
            price: Limit price (ignored for market orders)
            order_type: "limit" or "market"
            tif: Time in force - "Gtc" (Good til Cancel), "Ioc" (Immediate or Cancel),
                 "Alo" (Add Liquidity Only)
            reduce_only: If True, order can only reduce existing position
            cloid: Client order ID for tracking (optional)

        Returns:
            Dict containing:
                - success: bool
                - order_id: int (if successful)
                - status: str
                - response: dict (full exchange response)
                - error: str (if failed)

        Raises:
            ValueError: If input validation fails
        """
        try:
            # Input validation
            if size <= 0:
                raise ValueError(f"Order size must be positive, got {size}")

            if order_type not in ["limit", "market"]:
                raise ValueError(f"Invalid order_type: {order_type}. Must be 'limit' or 'market'")

            if tif not in ["Gtc", "Ioc", "Alo"]:
                raise ValueError(f"Invalid time in force: {tif}. Must be 'Gtc', 'Ioc', or 'Alo'")

            # Prepare order parameters
            order_params = {
                "coin": coin,
                "is_buy": is_buy,
                "sz": size,
                "limit_px": price,
                "order_type": {"limit": "limit", "market": "market"}[order_type],
                "reduce_only": reduce_only
            }

            # Add time in force for limit orders
            if order_type == "limit":
                order_params["tif"] = tif

            # Add client order ID if provided
            if cloid:
                order_params["cloid"] = cloid

            # Execute order
            response = self.exchange.order(
                coin=coin,
                is_buy=is_buy,
                sz=size,
                limit_px=price,
                order_type=order_params["order_type"],
                reduce_only=reduce_only,
                **({
                    "tif": tif
                } if order_type == "limit" else {}),
                **({
                    "cloid": cloid
                } if cloid else {})
            )

            # Parse response
            if response and response.get("status") == "ok":
                result = response.get("response", {})
                return {
                    "success": True,
                    "order_id": result.get("data", {}).get("statuses", [{}])[0].get("resting", {}).get("oid"),
                    "status": "placed",
                    "coin": coin,
                    "side": "buy" if is_buy else "sell",
                    "size": size,
                    "price": price,
                    "order_type": order_type,
                    "tif": tif,
                    "reduce_only": reduce_only,
                    "cloid": cloid,
                    "timestamp": datetime.utcnow().isoformat(),
                    "response": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("response", "Unknown error"),
                    "coin": coin,
                    "timestamp": datetime.utcnow().isoformat()
                }

        except ValueError as ve:
            return {
                "success": False,
                "error": f"Validation error: {str(ve)}",
                "coin": coin,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Order placement failed: {str(e)}",
                "coin": coin,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def place_batch_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Place multiple orders in a single batch request.

        Args:
            orders: List of order dictionaries, each containing:
                - coin: str
                - is_buy: bool
                - size: float
                - price: float
                - order_type: str (optional, default "limit")
                - tif: str (optional, default "Gtc")
                - reduce_only: bool (optional, default False)
                - cloid: str (optional)

        Returns:
            List of result dictionaries, one per order, each containing:
                - success: bool
                - order_id: int (if successful)
                - status: str
                - error: str (if failed)
                - order_index: int (position in batch)

        Example:
            orders = [
                {"coin": "BTC", "is_buy": True, "size": 0.1, "price": 50000},
                {"coin": "ETH", "is_buy": False, "size": 1.0, "price": 3000}
            ]
            results = await place_batch_orders(orders)
        """
        try:
            if not orders:
                return [{
                    "success": False,
                    "error": "No orders provided",
                    "timestamp": datetime.utcnow().isoformat()
                }]

            # Validate all orders first
            validated_orders = []
            for idx, order in enumerate(orders):
                try:
                    # Extract parameters with defaults
                    coin = order.get("coin")
                    is_buy = order.get("is_buy")
                    size = order.get("size")
                    price = order.get("price")

                    if not all([coin, is_buy is not None, size, price]):
                        raise ValueError("Missing required fields: coin, is_buy, size, price")

                    order_type = order.get("order_type", "limit")
                    tif = order.get("tif", "Gtc")
                    reduce_only = order.get("reduce_only", False)
                    cloid = order.get("cloid")

                    # Validate
                    if size <= 0:
                        raise ValueError(f"Order size must be positive, got {size}")

                    validated_order = {
                        "coin": coin,
                        "is_buy": is_buy,
                        "sz": size,
                        "limit_px": price,
                        "order_type": order_type,
                        "reduce_only": reduce_only,
                        "order_index": idx
                    }

                    if order_type == "limit":
                        validated_order["tif"] = tif

                    if cloid:
                        validated_order["cloid"] = cloid

                    validated_orders.append(validated_order)

                except Exception as e:
                    validated_orders.append({
                        "error": str(e),
                        "order_index": idx,
                        "success": False
                    })

            # Execute batch order
            batch_response = self.exchange.bulk_orders(validated_orders)

            # Parse results
            results = []
            if batch_response and batch_response.get("status") == "ok":
                response_data = batch_response.get("response", {}).get("data", {})
                statuses = response_data.get("statuses", [])

                for idx, (order, status) in enumerate(zip(orders, statuses)):
                    if status.get("resting"):
                        results.append({
                            "success": True,
                            "order_id": status["resting"].get("oid"),
                            "status": "placed",
                            "coin": order.get("coin"),
                            "side": "buy" if order.get("is_buy") else "sell",
                            "size": order.get("size"),
                            "price": order.get("price"),
                            "order_index": idx,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    else:
                        results.append({
                            "success": False,
                            "error": status.get("error", "Order not resting"),
                            "coin": order.get("coin"),
                            "order_index": idx,
                            "timestamp": datetime.utcnow().isoformat()
                        })
            else:
                # All orders failed
                for idx, order in enumerate(orders):
                    results.append({
                        "success": False,
                        "error": batch_response.get("response", "Batch order failed"),
                        "coin": order.get("coin"),
                        "order_index": idx,
                        "timestamp": datetime.utcnow().isoformat()
                    })

            return results

        except Exception as e:
            return [{
                "success": False,
                "error": f"Batch order execution failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }]

    async def cancel_order(
        self,
        coin: str,
        order_id: Optional[int] = None,
        cloid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel a specific order by order ID or client order ID.

        Args:
            coin: Trading pair symbol
            order_id: Exchange order ID (optional if cloid provided)
            cloid: Client order ID (optional if order_id provided)

        Returns:
            Dict containing:
                - success: bool
                - order_id: int (canceled order ID)
                - status: str
                - response: dict (full exchange response)
                - error: str (if failed)

        Raises:
            ValueError: If neither order_id nor cloid is provided
        """
        try:
            if not order_id and not cloid:
                raise ValueError("Must provide either order_id or cloid")

            # Prepare cancellation request
            cancel_params = {"coin": coin}

            if order_id:
                cancel_params["oid"] = order_id
            elif cloid:
                cancel_params["cloid"] = cloid

            # Execute cancellation
            response = self.exchange.cancel(
                coin=coin,
                oid=order_id if order_id else None,
                **({
                    "cloid": cloid
                } if cloid and not order_id else {})
            )

            # Parse response
            if response and response.get("status") == "ok":
                return {
                    "success": True,
                    "order_id": order_id,
                    "cloid": cloid,
                    "coin": coin,
                    "status": "canceled",
                    "timestamp": datetime.utcnow().isoformat(),
                    "response": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("response", "Cancellation failed"),
                    "order_id": order_id,
                    "cloid": cloid,
                    "coin": coin,
                    "timestamp": datetime.utcnow().isoformat()
                }

        except ValueError as ve:
            return {
                "success": False,
                "error": f"Validation error: {str(ve)}",
                "coin": coin,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Order cancellation failed: {str(e)}",
                "coin": coin,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def cancel_all_orders(self, coin: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel all open orders, optionally filtered by coin.

        Args:
            coin: Trading pair symbol (if None, cancels ALL orders across all coins)

        Returns:
            Dict containing:
                - success: bool
                - canceled_count: int (number of orders canceled)
                - orders: list (details of canceled orders)
                - status: str
                - error: str (if failed)

        Warning:
            If coin is None, this will cancel ALL open orders on the account.
            Use with caution.
        """
        try:
            # Get all open orders
            open_orders_response = self.info.open_orders(self.account)

            if not open_orders_response:
                return {
                    "success": True,
                    "canceled_count": 0,
                    "orders": [],
                    "status": "no_open_orders",
                    "coin": coin,
                    "timestamp": datetime.utcnow().isoformat()
                }

            # Filter by coin if specified
            orders_to_cancel = []
            for order in open_orders_response:
                if coin is None or order.get("coin") == coin:
                    orders_to_cancel.append(order)

            if not orders_to_cancel:
                return {
                    "success": True,
                    "canceled_count": 0,
                    "orders": [],
                    "status": "no_matching_orders",
                    "coin": coin,
                    "timestamp": datetime.utcnow().isoformat()
                }

            # Cancel all matching orders
            canceled_orders = []
            failed_cancellations = []

            for order in orders_to_cancel:
                try:
                    order_coin = order.get("coin")
                    order_id = order.get("oid")

                    cancel_response = self.exchange.cancel(
                        coin=order_coin,
                        oid=order_id
                    )

                    if cancel_response and cancel_response.get("status") == "ok":
                        canceled_orders.append({
                            "coin": order_coin,
                            "order_id": order_id,
                            "side": order.get("side"),
                            "size": order.get("sz"),
                            "price": order.get("limitPx")
                        })
                    else:
                        failed_cancellations.append({
                            "coin": order_coin,
                            "order_id": order_id,
                            "error": cancel_response.get("response", "Unknown error")
                        })

                except Exception as e:
                    failed_cancellations.append({
                        "coin": order.get("coin"),
                        "order_id": order.get("oid"),
                        "error": str(e)
                    })

            return {
                "success": len(failed_cancellations) == 0,
                "canceled_count": len(canceled_orders),
                "failed_count": len(failed_cancellations),
                "orders": canceled_orders,
                "failed_orders": failed_cancellations if failed_cancellations else None,
                "status": "completed" if not failed_cancellations else "partial",
                "coin": coin,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Cancel all orders failed: {str(e)}",
                "coin": coin,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def modify_order(
        self,
        coin: str,
        order_id: int,
        new_price: Optional[float] = None,
        new_size: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Modify an existing order's price and/or size.

        Args:
            coin: Trading pair symbol
            order_id: Exchange order ID to modify
            new_price: New limit price (optional)
            new_size: New order size (optional)

        Returns:
            Dict containing:
                - success: bool
                - order_id: int (modified order ID)
                - modifications: dict (what was changed)
                - status: str
                - error: str (if failed)

        Raises:
            ValueError: If neither new_price nor new_size is provided

        Note:
            On Hyperliquid, modifying an order may result in a new order ID
            as it could cancel and replace the original order.
        """
        try:
            if new_price is None and new_size is None:
                raise ValueError("Must provide at least one of new_price or new_size")

            if new_size is not None and new_size <= 0:
                raise ValueError(f"New size must be positive, got {new_size}")

            # Prepare modification parameters
            modify_params = {
                "coin": coin,
                "oid": order_id
            }

            if new_price is not None:
                modify_params["limit_px"] = new_price

            if new_size is not None:
                modify_params["sz"] = new_size

            # Execute modification
            response = self.exchange.modify_order(
                coin=coin,
                oid=order_id,
                **({
                    "limit_px": new_price
                } if new_price is not None else {}),
                **({
                    "sz": new_size
                } if new_size is not None else {})
            )

            # Parse response
            if response and response.get("status") == "ok":
                modifications = {}
                if new_price is not None:
                    modifications["price"] = new_price
                if new_size is not None:
                    modifications["size"] = new_size

                return {
                    "success": True,
                    "order_id": order_id,
                    "coin": coin,
                    "modifications": modifications,
                    "status": "modified",
                    "timestamp": datetime.utcnow().isoformat(),
                    "response": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("response", "Modification failed"),
                    "order_id": order_id,
                    "coin": coin,
                    "timestamp": datetime.utcnow().isoformat()
                }

        except ValueError as ve:
            return {
                "success": False,
                "error": f"Validation error: {str(ve)}",
                "order_id": order_id,
                "coin": coin,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Order modification failed: {str(e)}",
                "order_id": order_id,
                "coin": coin,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def place_twap_order(
        self,
        coin: str,
        is_buy: bool,
        total_size: float,
        duration_minutes: int,
        randomize: bool = False
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
            Dict containing:
                - success: bool
                - twap_id: str (TWAP order identifier)
                - total_size: float
                - duration_minutes: int
                - estimated_slices: int (approximate number of child orders)
                - status: str
                - error: str (if failed)

        Note:
            TWAP orders are automatically managed by the exchange. The actual
            number and timing of slices is determined by the exchange algorithm.
        """
        try:
            # Input validation
            if total_size <= 0:
                raise ValueError(f"Total size must be positive, got {total_size}")

            if duration_minutes <= 0:
                raise ValueError(f"Duration must be positive, got {duration_minutes}")

            # Estimate number of slices (typically 1 per minute)
            estimated_slices = max(1, duration_minutes)

            # Prepare TWAP parameters
            twap_params = {
                "coin": coin,
                "is_buy": is_buy,
                "sz": total_size,
                "duration": duration_minutes * 60,  # Convert to seconds
                "randomize": randomize
            }

            # Execute TWAP order
            response = self.exchange.twap_order(
                coin=coin,
                is_buy=is_buy,
                sz=total_size,
                duration=duration_minutes * 60,
                randomize=randomize
            )

            # Parse response
            if response and response.get("status") == "ok":
                twap_data = response.get("response", {}).get("data", {})

                return {
                    "success": True,
                    "twap_id": twap_data.get("twap_id", f"twap_{int(time.time())}"),
                    "coin": coin,
                    "side": "buy" if is_buy else "sell",
                    "total_size": total_size,
                    "duration_minutes": duration_minutes,
                    "estimated_slices": estimated_slices,
                    "randomize": randomize,
                    "status": "active",
                    "start_time": datetime.utcnow().isoformat(),
                    "estimated_end_time": (
                        datetime.utcnow() + timedelta(minutes=duration_minutes)
                    ).isoformat(),
                    "response": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("response", "TWAP order creation failed"),
                    "coin": coin,
                    "timestamp": datetime.utcnow().isoformat()
                }

        except ValueError as ve:
            return {
                "success": False,
                "error": f"Validation error: {str(ve)}",
                "coin": coin,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"TWAP order placement failed: {str(e)}",
                "coin": coin,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def adjust_leverage(
        self,
        coin: str,
        leverage: int,
        is_cross: bool = True
    ) -> Dict[str, Any]:
        """
        Adjust leverage for a perpetual trading pair.

        Args:
            coin: Trading pair symbol
            leverage: Leverage multiplier (e.g., 10 for 10x)
            is_cross: True for cross margin, False for isolated margin

        Returns:
            Dict containing:
                - success: bool
                - coin: str
                - leverage: int
                - margin_mode: str ("cross" or "isolated")
                - status: str
                - error: str (if failed)

        Warning:
            Higher leverage increases both potential profits and losses.
            Ensure you understand the risks before using high leverage.

        Note:
            Maximum leverage varies by asset. Common limits:
            - BTC/ETH: 50x
            - Altcoins: 20-30x
        """
        try:
            # Input validation
            if leverage <= 0:
                raise ValueError(f"Leverage must be positive, got {leverage}")

            if leverage > 50:
                raise ValueError(f"Leverage {leverage}x exceeds typical maximum of 50x")

            # Execute leverage update
            response = self.exchange.update_leverage(
                coin=coin,
                leverage=leverage,
                is_cross=is_cross
            )

            # Parse response
            if response and response.get("status") == "ok":
                return {
                    "success": True,
                    "coin": coin,
                    "leverage": leverage,
                    "margin_mode": "cross" if is_cross else "isolated",
                    "status": "updated",
                    "timestamp": datetime.utcnow().isoformat(),
                    "response": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("response", "Leverage update failed"),
                    "coin": coin,
                    "timestamp": datetime.utcnow().isoformat()
                }

        except ValueError as ve:
            return {
                "success": False,
                "error": f"Validation error: {str(ve)}",
                "coin": coin,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Leverage adjustment failed: {str(e)}",
                "coin": coin,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def modify_isolated_margin(
        self,
        coin: str,
        amount: float,
        is_add: bool = True
    ) -> Dict[str, Any]:
        """
        Add or remove USDC from an isolated margin position.

        Args:
            coin: Trading pair symbol
            amount: Amount of USDC to add or remove
            is_add: True to add margin, False to remove margin

        Returns:
            Dict containing:
                - success: bool
                - coin: str
                - amount: float
                - action: str ("added" or "removed")
                - new_margin: float (if available)
                - status: str
                - error: str (if failed)

        Note:
            This only works for positions in isolated margin mode.
            For cross margin positions, use adjust_leverage() to switch
            to isolated mode first.

        Warning:
            Removing too much margin may trigger liquidation if position
            margin falls below maintenance requirements.
        """
        try:
            # Input validation
            if amount <= 0:
                raise ValueError(f"Amount must be positive, got {amount}")

            # Execute margin update
            response = self.exchange.update_isolated_margin(
                coin=coin,
                is_buy=is_add,
                ntli=amount  # Note: ntli = notional transfer leverage isolated
            )

            # Parse response
            if response and response.get("status") == "ok":
                return {
                    "success": True,
                    "coin": coin,
                    "amount": amount,
                    "action": "added" if is_add else "removed",
                    "status": "updated",
                    "timestamp": datetime.utcnow().isoformat(),
                    "response": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("response", "Isolated margin update failed"),
                    "coin": coin,
                    "timestamp": datetime.utcnow().isoformat()
                }

        except ValueError as ve:
            return {
                "success": False,
                "error": f"Validation error: {str(ve)}",
                "coin": coin,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Isolated margin modification failed: {str(e)}",
                "coin": coin,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def update_dead_mans_switch(self, delay_seconds: int) -> Dict[str, Any]:
        """
        Configure dead man's switch to auto-cancel all orders after a delay.

        The dead man's switch is a safety mechanism that automatically cancels
        all open orders if not refreshed within the specified delay. This is
        useful for preventing runaway orders if your trading bot crashes or
        loses connection.

        Args:
            delay_seconds: Time in seconds before auto-canceling (minimum 5)

        Returns:
            Dict containing:
                - success: bool
                - delay_seconds: int
                - trigger_time: str (ISO timestamp when switch will trigger)
                - status: str
                - error: str (if failed)

        Note:
            You must call this method periodically (before the delay expires)
            to prevent the switch from triggering. Common pattern is to call
            this every time you successfully communicate with the exchange.

        Warning:
            If the delay expires, ALL open orders will be canceled immediately.
            Set the delay high enough to account for network latency and
            temporary disconnections.
        """
        try:
            # Input validation
            if delay_seconds < 5:
                raise ValueError(
                    f"Delay must be at least 5 seconds, got {delay_seconds}"
                )

            # Execute dead man's switch update
            response = self.exchange.update_dead_mans_switch(
                timeout=delay_seconds
            )

            # Calculate trigger time
            trigger_time = datetime.utcnow() + timedelta(seconds=delay_seconds)

            # Parse response
            if response and response.get("status") == "ok":
                return {
                    "success": True,
                    "delay_seconds": delay_seconds,
                    "trigger_time": trigger_time.isoformat(),
                    "status": "armed",
                    "timestamp": datetime.utcnow().isoformat(),
                    "response": response
                }
            else:
                return {
                    "success": False,
                    "error": response.get("response", "Dead man's switch update failed"),
                    "timestamp": datetime.utcnow().isoformat()
                }

        except ValueError as ve:
            return {
                "success": False,
                "error": f"Validation error: {str(ve)}",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Dead man's switch update failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
