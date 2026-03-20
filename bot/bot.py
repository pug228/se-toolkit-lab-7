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

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
from handlers.intent_router import route_intent, route_intent_async


def handle_message(message: str) -> str:
    """
    Route a message to the appropriate handler.

    Slash commands go to specific handlers.
    Plain text goes to the LLM intent router.
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
        # Route to LLM for natural language understanding
        return route_intent(message)


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

    # Add inline keyboard buttons for common actions
    keyboard = [
        [
            InlineKeyboardButton("📋 Available Labs", callback_data="labs"),
            InlineKeyboardButton("💊 Health Check", callback_data="health"),
        ],
        [
            InlineKeyboardButton("📊 Scores", callback_data="scores"),
            InlineKeyboardButton("❓ Help", callback_data="help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(response, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command from Telegram."""
    response = handle_help("")

    # Add inline keyboard buttons
    keyboard = [
        [
            InlineKeyboardButton("📋 Available Labs", callback_data="labs"),
            InlineKeyboardButton("💊 Health Check", callback_data="health"),
        ],
        [
            InlineKeyboardButton("📊 Scores for lab-04", callback_data="scores_lab-04"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(response, reply_markup=reply_markup)


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
    """Handle plain text messages from Telegram using LLM intent routing."""
    text = update.message.text
    response = await route_intent_async(text)
    await update.message.reply_text(response)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button callbacks."""
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "labs":
        response = await handle_labs_async("")
    elif callback_data == "health":
        response = await handle_health_async("")
    elif callback_data == "help":
        response = handle_help("")
    elif callback_data.startswith("scores"):
        # Extract lab from callback data like "scores_lab-04"
        parts = callback_data.split("_")
        lab = parts[1] if len(parts) > 1 else "lab-04"
        response = await handle_scores_async(lab)
    else:
        response = "Please select an option from the menu."

    await query.edit_message_text(response)


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

    # Create application with optional proxy support and increased timeouts
    from telegram.request import HTTPXRequest

    builder = Application.builder().token(config.bot_token)

    # Configure request with longer timeouts for unstable connections
    request = HTTPXRequest(
        connect_timeout=30.0,  # Connection timeout (was 10s)
        read_timeout=60.0,  # Read timeout (was 10s)
        write_timeout=30.0,  # Write timeout (was 10s)
        pool_timeout=30.0,  # Pool timeout (was 10s)
    )
    builder = builder.request(request)

    if config.proxy_url:
        builder = builder.proxy_url(config.proxy_url)

    app = builder.build()

    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(CommandHandler("labs", labs_command))
    app.add_handler(CommandHandler("scores", scores_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )
    # Add callback handler for inline keyboard buttons
    from telegram.ext import CallbackQueryHandler

    app.add_handler(CallbackQueryHandler(button_callback))

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
