#!/usr/bin/env python3
"""
Hyperliquid MCP Server Setup Script
Automates installation and configuration of the MCP server for Claude Desktop
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(message):
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")

def check_python_version():
    """Ensure Python 3.8+ is being used"""
    print_header("Checking Python Version")

    if sys.version_info < (3, 8):
        print_error(f"Python 3.8+ required. Current version: {sys.version}")
        sys.exit(1)

    print_success(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected")

def create_virtual_environment():
    """Create Python virtual environment"""
    print_header("Creating Virtual Environment")

    venv_path = Path("venv")

    if venv_path.exists():
        print_warning("Virtual environment already exists, skipping creation")
        return

    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print_success("Virtual environment created at ./venv")
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")
        sys.exit(1)

def install_dependencies():
    """Install Python dependencies from requirements.txt"""
    print_header("Installing Dependencies")

    pip_path = Path("venv/bin/pip")
    if not pip_path.exists():
        pip_path = Path("venv/Scripts/pip.exe")  # Windows

    if not pip_path.exists():
        print_error("Could not find pip in virtual environment")
        sys.exit(1)

    try:
        print_info("Upgrading pip...")
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)

        print_info("Installing requirements...")
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)

        print_success("All dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        sys.exit(1)

def setup_environment_file():
    """Copy .env.example to .env if it doesn't exist"""
    print_header("Setting Up Environment Variables")

    env_file = Path(".env")
    env_example = Path(".env.example")

    if env_file.exists():
        print_warning(".env file already exists, skipping creation")
        print_info("Please ensure your .env file has the required variables:")
        print("  - HYPERLIQUID_PRIVATE_KEY")
        print("  - HYPERLIQUID_ACCOUNT_ADDRESS")
        return

    if not env_example.exists():
        print_error(".env.example not found")
        sys.exit(1)

    shutil.copy(env_example, env_file)
    print_success(".env file created from .env.example")
    print_warning("IMPORTANT: Edit .env and add your Hyperliquid credentials!")

def generate_claude_config():
    """Generate claude_desktop_config.json"""
    print_header("Generating Claude Desktop Configuration")

    project_path = Path.cwd().absolute()
    venv_python = project_path / "venv" / "bin" / "python"
    server_path = project_path / "server.py"

    # Check if server.py exists
    if not server_path.exists():
        print_error("server.py not found in project directory")
        sys.exit(1)

    config = {
        "mcpServers": {
            "hyperliquid-mcp-server": {
                "command": str(venv_python),
                "args": [str(server_path)],
                "env": {
                    "HYPERLIQUID_PRIVATE_KEY": "${HYPERLIQUID_PRIVATE_KEY}",
                    "HYPERLIQUID_ACCOUNT_ADDRESS": "${HYPERLIQUID_ACCOUNT_ADDRESS}",
                    "HYPERLIQUID_NETWORK": "mainnet",
                    "LOG_LEVEL": "INFO"
                }
            }
        }
    }

    config_path = project_path / "claude_desktop_config.json"

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print_success(f"Configuration generated at {config_path}")

def update_claude_desktop_config():
    """Update Claude Desktop's global configuration"""
    print_header("Updating Claude Desktop Configuration")

    # Claude Desktop config path on macOS
    claude_config_dir = Path.home() / "Library" / "Application Support" / "Claude"
    claude_config_path = claude_config_dir / "claude_desktop_config.json"

    if not claude_config_dir.exists():
        print_warning("Claude Desktop config directory not found")
        print_info("You may need to manually install the MCP server configuration")
        print_info(f"Copy claude_desktop_config.json to: {claude_config_path}")
        return

    project_path = Path.cwd().absolute()
    local_config_path = project_path / "claude_desktop_config.json"

    if not local_config_path.exists():
        print_error("Local claude_desktop_config.json not found")
        return

    # Read local config
    with open(local_config_path, "r") as f:
        new_server_config = json.load(f)

    # Read or create Claude Desktop config
    if claude_config_path.exists():
        with open(claude_config_path, "r") as f:
            claude_config = json.load(f)
    else:
        claude_config = {"mcpServers": {}}

    # Ensure mcpServers exists
    if "mcpServers" not in claude_config:
        claude_config["mcpServers"] = {}

    # Update with new server
    claude_config["mcpServers"].update(new_server_config["mcpServers"])

    # Backup existing config
    if claude_config_path.exists():
        backup_path = claude_config_path.with_suffix(".json.backup")
        shutil.copy(claude_config_path, backup_path)
        print_info(f"Backup created at {backup_path}")

    # Write updated config
    with open(claude_config_path, "w") as f:
        json.dump(claude_config, f, indent=2)

    print_success(f"Claude Desktop config updated at {claude_config_path}")
    print_warning("Please restart Claude Desktop to load the new MCP server")

def test_mcp_server():
    """Test MCP server connectivity"""
    print_header("Testing MCP Server")

    print_info("Skipping connectivity test (requires .env configuration)")
    print_info("After configuring .env, you can test with:")
    print(f"  {Colors.OKCYAN}mcp dev server.py{Colors.ENDC}")

def print_next_steps():
    """Print next steps for the user"""
    print_header("Setup Complete!")

    print(f"{Colors.OKGREEN}{Colors.BOLD}Next Steps:{Colors.ENDC}\n")

    print(f"{Colors.BOLD}1. Configure your credentials:{Colors.ENDC}")
    print(f"   Edit {Colors.OKCYAN}.env{Colors.ENDC} and add:")
    print(f"   - HYPERLIQUID_PRIVATE_KEY (your Ethereum private key)")
    print(f"   - HYPERLIQUID_ACCOUNT_ADDRESS (your wallet address)\n")

    print(f"{Colors.BOLD}2. Test the MCP server:{Colors.ENDC}")
    print(f"   {Colors.OKCYAN}mcp dev server.py{Colors.ENDC}\n")

    print(f"{Colors.BOLD}3. Restart Claude Desktop:{Colors.ENDC}")
    print(f"   Quit and reopen Claude Desktop to load the MCP server\n")

    print(f"{Colors.BOLD}4. Verify in Claude:{Colors.ENDC}")
    print(f"   Ask: {Colors.OKCYAN}\"What Hyperliquid tools do you have available?\"{Colors.ENDC}\n")

    print(f"{Colors.BOLD}5. Start trading:{Colors.ENDC}")
    print(f"   Example: {Colors.OKCYAN}\"Show me my current positions on Hyperliquid\"{Colors.ENDC}\n")

    print(f"{Colors.WARNING}{Colors.BOLD}Security Reminder:{Colors.ENDC}")
    print(f"   - Never commit your {Colors.FAIL}.env{Colors.ENDC} file")
    print(f"   - Keep your private key secure")
    print(f"   - Use testnet for development\n")

def main():
    """Main setup function"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                                                            ║")
    print("║        Hyperliquid MCP Server Setup                        ║")
    print("║        Complete Trading Integration for Claude             ║")
    print("║                                                            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")

    try:
        check_python_version()
        create_virtual_environment()
        install_dependencies()
        setup_environment_file()
        generate_claude_config()
        update_claude_desktop_config()
        test_mcp_server()
        print_next_steps()

    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Setup interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
