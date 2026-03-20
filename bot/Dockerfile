# Bot Dockerfile - uses uv and pyproject.toml (no requirements.txt)
FROM python:3.14-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy bot project files
COPY pyproject.toml uv.lock ./

# Sync dependencies using uv (no pip, no requirements.txt)
RUN uv sync --frozen

# Copy bot source code
COPY . .

# Run the bot
CMD ["uv", "run", "bot.py"]
