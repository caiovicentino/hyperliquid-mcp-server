"""
Hyperliquid WebSocket Tools

Provides real-time WebSocket connectivity for:
- User events (fills, funding, liquidations)
- Market data streams (L2 orderbook, trades, candles)
- Order updates and fills
- Subscription management with auto-reconnection
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from enum import Enum
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)


class SubscriptionType(Enum):
    """WebSocket subscription types"""
    USER_EVENTS = "userEvents"
    L2_BOOK = "l2Book"
    TRADES = "trades"
    CANDLE = "candle"
    ORDER_UPDATES = "orderUpdates"
    USER_FILLS = "userFills"


class WebSocketManager:
    """
    Manages persistent WebSocket connection with auto-reconnection
    """

    def __init__(self, url: str, user_address: Optional[str] = None):
        """
        Initialize WebSocket manager

        Args:
            url: WebSocket URL (wss://api.hyperliquid.xyz/ws)
            user_address: User's wallet address for authenticated subscriptions
        """
        self.url = url
        self.user_address = user_address
        self.ws = None
        self.connected = False
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.base_reconnect_delay = 1.0
        self.message_queue = asyncio.Queue()
        self.running = False
        self.stats = {
            "messages_received": 0,
            "messages_sent": 0,
            "reconnections": 0,
            "last_message_time": None,
            "connection_start_time": None
        }

        logger.info(f"WebSocketManager initialized with URL: {url}")

    async def connect(self):
        """Establish WebSocket connection"""
        try:
            logger.info(f"Connecting to WebSocket: {self.url}")
            self.ws = await websockets.connect(
                self.url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            self.connected = True
            self.reconnect_attempts = 0
            self.stats["connection_start_time"] = datetime.now().isoformat()
            logger.info("WebSocket connected successfully")

            # Resubscribe to all active subscriptions
            await self._resubscribe_all()

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.connected = False
            raise

    async def disconnect(self):
        """Close WebSocket connection"""
        try:
            self.running = False
            if self.ws:
                await self.ws.close()
                logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
        finally:
            self.connected = False
            self.ws = None

    async def reconnect(self):
        """Reconnect with exponential backoff"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached")
            raise Exception("Failed to reconnect after maximum attempts")

        self.reconnect_attempts += 1
        delay = self.base_reconnect_delay * (2 ** (self.reconnect_attempts - 1))

        logger.warning(f"Reconnecting in {delay}s (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
        await asyncio.sleep(delay)

        try:
            await self.connect()
            self.stats["reconnections"] += 1
        except Exception as e:
            logger.error(f"Reconnection attempt {self.reconnect_attempts} failed: {e}")
            await self.reconnect()

    async def _resubscribe_all(self):
        """Resubscribe to all active subscriptions after reconnection"""
        if not self.subscriptions:
            return

        logger.info(f"Resubscribing to {len(self.subscriptions)} active subscriptions")
        for sub_id, sub_data in self.subscriptions.items():
            try:
                await self._send_message(sub_data["message"])
                logger.debug(f"Resubscribed to {sub_id}")
            except Exception as e:
                logger.error(f"Failed to resubscribe to {sub_id}: {e}")

    async def _send_message(self, message: Dict[str, Any]):
        """Send message to WebSocket"""
        if not self.connected or not self.ws:
            raise Exception("WebSocket not connected")

        try:
            message_json = json.dumps(message)
            await self.ws.send(message_json)
            self.stats["messages_sent"] += 1
            logger.debug(f"Sent message: {message_json}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    async def subscribe(
        self,
        subscription_type: str,
        params: Dict[str, Any],
        callback: Optional[Callable] = None
    ) -> str:
        """
        Subscribe to a WebSocket channel

        Args:
            subscription_type: Type of subscription
            params: Subscription parameters
            callback: Optional callback function for messages

        Returns:
            Subscription ID
        """
        # Create subscription message
        subscription = {
            "type": subscription_type,
            **params
        }

        message = {
            "method": "subscribe",
            "subscription": subscription
        }

        # Generate subscription ID
        sub_id = f"{subscription_type}_{hash(json.dumps(params, sort_keys=True))}"

        # Store subscription
        self.subscriptions[sub_id] = {
            "type": subscription_type,
            "params": params,
            "message": message,
            "callback": callback,
            "messages_received": 0,
            "subscribed_at": datetime.now().isoformat()
        }

        # Register callback
        if callback:
            if sub_id not in self.message_handlers:
                self.message_handlers[sub_id] = []
            self.message_handlers[sub_id].append(callback)

        # Send subscription message
        try:
            await self._send_message(message)
            logger.info(f"Subscribed to {subscription_type} with ID: {sub_id}")
            return sub_id
        except Exception as e:
            del self.subscriptions[sub_id]
            raise Exception(f"Failed to subscribe: {str(e)}")

    async def unsubscribe(self, sub_id: str):
        """Unsubscribe from a channel"""
        if sub_id not in self.subscriptions:
            raise ValueError(f"Subscription {sub_id} not found")

        sub_data = self.subscriptions[sub_id]

        message = {
            "method": "unsubscribe",
            "subscription": {
                "type": sub_data["type"],
                **sub_data["params"]
            }
        }

        try:
            await self._send_message(message)
            del self.subscriptions[sub_id]
            if sub_id in self.message_handlers:
                del self.message_handlers[sub_id]
            logger.info(f"Unsubscribed from {sub_id}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {sub_id}: {e}")
            raise

    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            self.stats["messages_received"] += 1
            self.stats["last_message_time"] = datetime.now().isoformat()

            # Route message to appropriate handlers
            channel = data.get("channel", "")

            for sub_id, sub_data in self.subscriptions.items():
                # Check if message belongs to this subscription
                if self._message_matches_subscription(data, sub_data):
                    sub_data["messages_received"] += 1

                    # Call registered callbacks
                    if sub_id in self.message_handlers:
                        for handler in self.message_handlers[sub_id]:
                            try:
                                if asyncio.iscoroutinefunction(handler):
                                    await handler(data)
                                else:
                                    handler(data)
                            except Exception as e:
                                logger.error(f"Error in message handler: {e}")

            # Add to message queue for polling
            await self.message_queue.put({
                "timestamp": datetime.now().isoformat(),
                "data": data
            })

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def _message_matches_subscription(
        self,
        message: Dict[str, Any],
        subscription: Dict[str, Any]
    ) -> bool:
        """Check if message matches subscription"""
        # This is a simple implementation - may need to be more sophisticated
        # based on actual Hyperliquid WebSocket protocol
        msg_type = message.get("channel", "").split("@")[0]
        sub_type = subscription.get("type", "")

        return msg_type.lower() == sub_type.lower()

    async def listen(self):
        """Main message listening loop"""
        self.running = True

        while self.running:
            try:
                if not self.connected:
                    await self.reconnect()

                message = await asyncio.wait_for(self.ws.recv(), timeout=30.0)
                await self._handle_message(message)

            except asyncio.TimeoutError:
                # No message received in timeout period - this is normal
                continue
            except ConnectionClosed as e:
                logger.warning(f"Connection closed: {e}")
                self.connected = False
                if self.running:
                    await self.reconnect()
            except WebSocketException as e:
                logger.error(f"WebSocket error: {e}")
                self.connected = False
                if self.running:
                    await self.reconnect()
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                if self.running:
                    await asyncio.sleep(1)

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "connected": self.connected,
            "subscriptions": len(self.subscriptions),
            "messages_received": self.stats["messages_received"],
            "messages_sent": self.stats["messages_sent"],
            "reconnections": self.stats["reconnections"],
            "last_message_time": self.stats["last_message_time"],
            "connection_start_time": self.stats["connection_start_time"],
            "reconnect_attempts": self.reconnect_attempts
        }


class WebSocketTools:
    """
    Tools for WebSocket streaming and real-time data.

    This class provides methods for:
    - Subscribing to real-time price feeds
    - Streaming order book updates
    - Monitoring account updates (fills, positions)
    - Managing WebSocket connections
    """

    def __init__(self, ws_url: str, account_address: Optional[str] = None):
        """
        Initialize WebSocket tools.

        Args:
            ws_url: WebSocket URL for Hyperliquid
            account_address: Optional account address for account-specific streams
        """
        self.ws_url = ws_url
        self.account_address = account_address
        self.logger = logging.getLogger(__name__)
        self.manager = WebSocketManager(ws_url, account_address)
        self.active_tasks: List[asyncio.Task] = []

        self.logger.info(f"WebSocketTools initialized with URL: {ws_url}")

    async def start(self):
        """Start WebSocket connection and listening"""
        await self.manager.connect()

        # Start listening task
        listen_task = asyncio.create_task(self.manager.listen())
        self.active_tasks.append(listen_task)

        logger.info("WebSocket tools started")

    async def stop(self):
        """Stop WebSocket connection and cleanup"""
        # Cancel all active tasks
        for task in self.active_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.active_tasks, return_exceptions=True)

        # Disconnect
        await self.manager.disconnect()

        logger.info("WebSocket tools stopped")

    async def subscribe_user_events(
        self,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Subscribe to user events (fills, funding, liquidations)

        Args:
            callback: Optional callback function called for each event

        Returns:
            Subscription ID

        Raises:
            ValueError: If user_address not provided
            Exception: If subscription fails
        """
        if not self.account_address:
            raise ValueError("User address required for user events subscription")

        params = {
            "user": self.account_address
        }

        try:
            sub_id = await self.manager.subscribe(
                SubscriptionType.USER_EVENTS.value,
                params,
                callback
            )
            logger.info(f"Subscribed to user events for {self.account_address}")
            return sub_id
        except Exception as e:
            logger.error(f"Failed to subscribe to user events: {e}")
            raise

    async def subscribe_market_data(
        self,
        coin: str,
        data_types: List[str],
        callback: Optional[Callable] = None
    ) -> List[str]:
        """
        Subscribe to market data streams

        Args:
            coin: Symbol to subscribe to (e.g., "BTC", "ETH")
            data_types: List of data types - "l2Book", "trades", "candle"
            callback: Optional callback function for updates

        Returns:
            List of subscription IDs

        Raises:
            ValueError: If invalid data_type provided
            Exception: If subscription fails
        """
        valid_types = ["l2Book", "trades", "candle"]
        for data_type in data_types:
            if data_type not in valid_types:
                raise ValueError(f"Invalid data type: {data_type}. Must be one of {valid_types}")

        subscription_ids = []

        for data_type in data_types:
            params = {
                "coin": coin
            }

            # Add interval for candle subscriptions
            if data_type == "candle":
                params["interval"] = "1m"  # Default to 1 minute

            try:
                sub_id = await self.manager.subscribe(
                    data_type,
                    params,
                    callback
                )
                subscription_ids.append(sub_id)
                logger.info(f"Subscribed to {data_type} for {coin}")
            except Exception as e:
                logger.error(f"Failed to subscribe to {data_type} for {coin}: {e}")
                # Unsubscribe from already created subscriptions
                for existing_sub_id in subscription_ids:
                    try:
                        await self.manager.unsubscribe(existing_sub_id)
                    except:
                        pass
                raise

        return subscription_ids

    async def subscribe_order_updates(
        self,
        callback: Optional[Callable] = None
    ) -> List[str]:
        """
        Subscribe to order updates and user fills

        Args:
            callback: Optional callback function for updates

        Returns:
            List of subscription IDs (orderUpdates and userFills)

        Raises:
            ValueError: If user_address not provided
            Exception: If subscription fails
        """
        if not self.account_address:
            raise ValueError("User address required for order updates subscription")

        subscription_ids = []

        # Subscribe to order updates
        try:
            params = {
                "user": self.account_address
            }

            # Subscribe to orderUpdates
            sub_id1 = await self.manager.subscribe(
                SubscriptionType.ORDER_UPDATES.value,
                params,
                callback
            )
            subscription_ids.append(sub_id1)

            # Subscribe to userFills
            sub_id2 = await self.manager.subscribe(
                SubscriptionType.USER_FILLS.value,
                params,
                callback
            )
            subscription_ids.append(sub_id2)

            logger.info(f"Subscribed to order updates for {self.account_address}")
            return subscription_ids

        except Exception as e:
            logger.error(f"Failed to subscribe to order updates: {e}")
            # Cleanup
            for sub_id in subscription_ids:
                try:
                    await self.manager.unsubscribe(sub_id)
                except:
                    pass
            raise

    def get_active_subscriptions(self) -> List[Dict[str, Any]]:
        """
        Get list of all active subscriptions

        Returns:
            List of subscription dictionaries with:
            - subscription_id: Unique subscription identifier
            - subscription_type: Type of subscription
            - params: Subscription parameters
            - connected: Connection status
            - messages_received: Number of messages received
            - subscribed_at: Subscription timestamp
        """
        subscriptions = []

        for sub_id, sub_data in self.manager.subscriptions.items():
            subscriptions.append({
                "subscription_id": sub_id,
                "subscription_type": sub_data["type"],
                "params": sub_data["params"],
                "connected": self.manager.connected,
                "messages_received": sub_data["messages_received"],
                "subscribed_at": sub_data["subscribed_at"]
            })

        return subscriptions

    async def unsubscribe(self, subscription_id: str):
        """
        Unsubscribe from a specific subscription

        Args:
            subscription_id: ID of subscription to remove

        Raises:
            ValueError: If subscription_id not found
            Exception: If unsubscribe fails
        """
        await self.manager.unsubscribe(subscription_id)

    async def unsubscribe_all(self):
        """Unsubscribe from all active subscriptions"""
        subscription_ids = list(self.manager.subscriptions.keys())

        for sub_id in subscription_ids:
            try:
                await self.manager.unsubscribe(sub_id)
            except Exception as e:
                logger.error(f"Failed to unsubscribe from {sub_id}: {e}")

        logger.info("Unsubscribed from all channels")

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get WebSocket connection statistics

        Returns:
            Dictionary with connection metrics
        """
        return self.manager.get_stats()

    async def get_next_message(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Poll for next message from queue

        Args:
            timeout: Maximum time to wait for message

        Returns:
            Message dictionary or None if timeout
        """
        try:
            message = await asyncio.wait_for(
                self.manager.message_queue.get(),
                timeout=timeout
            )
            return message
        except asyncio.TimeoutError:
            return None
