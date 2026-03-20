#!/usr/bin/env python3
"""
Telegram bot entry point with --test mode.

Usage:
    uv run bot.py --test "/start"    # Test mode: calls handlers directly
    uv run bot.py                    # Production: connects to Telegram
"""

import argparse
import sys


def handle_start(user_input: str = "") -> str:
    """Handle /start command - welcome message."""
    return "Welcome! I'm your LMS assistant bot. Use /help to see available commands."


def handle_help(user_input: str = "") -> str:
    """Handle /help command - list available commands."""
    return """Available commands:
/start - Welcome message
/help - Show this help
/health - Check backend status
/labs - List available labs
/scores <lab> - Show scores for a lab"""


def handle_health(user_input: str = "") -> str:
    """Handle /health command - backend status check."""
    # TODO: Task 2 - call backend API
    return "Backend status: OK (placeholder)"


def handle_labs(user_input: str = "") -> str:
    """Handle /labs command - list available labs."""
    # TODO: Task 2 - call backend API
    return "Available labs: (placeholder)"


def handle_scores(user_input: str = "") -> str:
    """Handle /scores command - show scores for a lab."""
    # TODO: Task 2 - call backend API
    if user_input:
        return f"Scores for {user_input}: (placeholder)"
    return "Please specify a lab, e.g., /scores lab-04"


def handle_message(message: str) -> str:
    """
    Route a message to the appropriate handler.
    
    In test mode, this is called directly with the test input.
    In production, Telegram messages are passed here.
    """
    if message.startswith("/start"):
        return handle_start(message[6:].strip())
    elif message.startswith("/help"):
        return handle_help(message[5:].strip())
    elif message.startswith("/health"):
        return handle_health(message[7:].strip())
    elif message.startswith("/labs"):
        return handle_labs(message[5:].strip())
    elif message.startswith("/scores"):
        return handle_scores(message[7:].strip())
    else:
        # TODO: Task 3 - route to LLM for natural language
        return "I didn't understand that. Try /help for available commands."


def run_test_mode(test_input: str) -> None:
    """
    Run in test mode: call handler directly and print result.
    
    No Telegram connection is made. Exit code is 0 on success.
    """
    response = handle_message(test_input)
    print(response)
    sys.exit(0)


def run_production_mode() -> None:
    """
    Run in production mode: connect to Telegram and listen for messages.
    
    TODO: Task 4 - implement Telegram bot loop
    """
    print("Production mode not yet implemented. Use --test for testing.")
    sys.exit(1)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LMS Telegram Bot")
    parser.add_argument(
        "--test",
        type=str,
        metavar="INPUT",
        help="Test mode: pass a command string and print response"
    )
    
    args = parser.parse_args()
    
    if args.test:
        run_test_mode(args.test)
    else:
        run_production_mode()


if __name__ == "__main__":
    main()
