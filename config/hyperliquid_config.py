"""Configuration module for Hyperliquid MCP Server."""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
# override=False means env vars from system/Claude Desktop take priority
load_dotenv(override=False)

# Network configuration
NETWORK = os.getenv("HYPERLIQUID_NETWORK", "mainnet")

# API endpoints
MAINNET_API_URL = "https://api.hyperliquid.xyz"
TESTNET_API_URL = "https://api.hyperliquid-testnet.xyz"

API_URL = MAINNET_API_URL if NETWORK == "mainnet" else TESTNET_API_URL

# WebSocket endpoints
MAINNET_WS_URL = "wss://api.hyperliquid.xyz/ws"
TESTNET_WS_URL = "wss://api.hyperliquid-testnet.xyz/ws"

WS_URL = MAINNET_WS_URL if NETWORK == "mainnet" else TESTNET_WS_URL

# Authentication credentials
PRIVATE_KEY = os.getenv("HYPERLIQUID_PRIVATE_KEY", "")
ACCOUNT_ADDRESS = os.getenv("HYPERLIQUID_ACCOUNT_ADDRESS", "")

# Additional configuration
DEFAULT_SLIPPAGE = float(os.getenv("HYPERLIQUID_DEFAULT_SLIPPAGE", "0.01"))  # 1% default
MAX_RETRY_ATTEMPTS = int(os.getenv("HYPERLIQUID_MAX_RETRY_ATTEMPTS", "3"))
REQUEST_TIMEOUT = int(os.getenv("HYPERLIQUID_REQUEST_TIMEOUT", "30"))  # seconds


def validate_config() -> tuple[bool, Optional[str]]:
    """
    Validate that all required configuration variables are set.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not PRIVATE_KEY:
        return False, "HYPERLIQUID_PRIVATE_KEY environment variable is required"

    if not ACCOUNT_ADDRESS:
        return False, "HYPERLIQUID_ACCOUNT_ADDRESS environment variable is required"

    if NETWORK not in ["mainnet", "testnet"]:
        return False, f"Invalid HYPERLIQUID_NETWORK value: {NETWORK}. Must be 'mainnet' or 'testnet'"

    # Validate private key format (should be hex string)
    if not PRIVATE_KEY.startswith("0x"):
        return False, "HYPERLIQUID_PRIVATE_KEY must start with '0x'"

    # Validate account address format (should be Ethereum-style address)
    if not ACCOUNT_ADDRESS.startswith("0x") or len(ACCOUNT_ADDRESS) != 42:
        return False, "HYPERLIQUID_ACCOUNT_ADDRESS must be a valid Ethereum address (0x...)"

    return True, None


def get_config_summary() -> str:
    """
    Get a summary of the current configuration.

    Returns:
        String representation of current configuration
    """
    return f"""Hyperliquid MCP Server Configuration:
- Network: {NETWORK}
- API URL: {API_URL}
- WebSocket URL: {WS_URL}
- Account Address: {ACCOUNT_ADDRESS[:6]}...{ACCOUNT_ADDRESS[-4:] if ACCOUNT_ADDRESS else 'Not set'}
- Private Key: {'Set' if PRIVATE_KEY else 'Not set'}
- Default Slippage: {DEFAULT_SLIPPAGE * 100}%
- Max Retry Attempts: {MAX_RETRY_ATTEMPTS}
- Request Timeout: {REQUEST_TIMEOUT}s
"""
