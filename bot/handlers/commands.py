"""
Command handlers for slash commands.

Each handler is a pure function: takes input string, returns response string.
No Telegram dependencies here - same function works from --test, tests, or Telegram.
"""


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
