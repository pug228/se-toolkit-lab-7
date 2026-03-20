#!/usr/bin/env python3
"""
Telegram bot entry point with --test mode.

Usage:
    uv run bot.py --test "/start"    # Test mode: calls handlers directly
    uv run bot.py                    # Production: connects to Telegram
"""

import argparse
import logging
import sys

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Import handlers from the handlers module
from handlers import (
    handle_start,
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
    handle_health_async,
    handle_labs_async,
    handle_scores_async,
)


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


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command from Telegram."""
    response = handle_start("")
    await update.message.reply_text(response)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command from Telegram."""
    response = handle_help("")
    await update.message.reply_text(response)


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /health command from Telegram."""
    response = await handle_health_async("")
    await update.message.reply_text(response)


async def labs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /labs command from Telegram."""
    response = await handle_labs_async("")
    await update.message.reply_text(response)


async def scores_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /scores command from Telegram."""
    arg = context.args[0] if context.args else ""
    response = await handle_scores_async(arg)
    await update.message.reply_text(response)


async def handle_text_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle plain text messages from Telegram."""
    text = update.message.text
    response = handle_message(text)
    await update.message.reply_text(response)


def run_production_mode() -> None:
    """
    Run in production mode: connect to Telegram and listen for messages.
    """
    from config import load_config

    config = load_config()

    if not config.bot_token:
        print("Error: BOT_TOKEN not found in .env.bot.secret")
        sys.exit(1)

    # Set up logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    # Create application
    app = Application.builder().token(config.bot_token).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(CommandHandler("labs", labs_command))
    app.add_handler(CommandHandler("scores", scores_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )

    # Start polling
    print("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LMS Telegram Bot")
    parser.add_argument(
        "--test",
        type=str,
        metavar="INPUT",
        help="Test mode: pass a command string and print response",
    )

    args = parser.parse_args()

    if args.test:
        run_test_mode(args.test)
    else:
        run_production_mode()


if __name__ == "__main__":
    main()
