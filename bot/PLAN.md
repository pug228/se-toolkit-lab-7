# Bot Development Plan

## Overview

This document outlines the development approach for building a Telegram bot that interacts with the LMS backend. The bot will support slash commands (`/start`, `/help`, `/health`, `/labs`, `/scores`) and understand plain text questions using an LLM for intent routing.

## Task 1: Scaffold and Test Mode

**Goal:** Create the project structure with a testable handler architecture.

**Approach:**
- Create `bot/` directory with `bot.py` as the entry point
- Implement `--test` mode that calls handlers directly without Telegram
- Separate handlers into their own module (`handlers/`) — these are plain functions that take input and return text
- Create `config.py` for environment variable loading from `.env.bot.secret`
- Set up `pyproject.toml` with bot dependencies

**Why this matters:** Testable handlers mean we can verify logic offline before deploying to Telegram. The same handler function works from `--test` mode, unit tests, or the Telegram bot.

## Task 2: Backend Integration

**Goal:** Connect handlers to the LMS backend API.

**Approach:**
- Create an API client in `services/api_client.py`
- Implement Bearer token authentication using `LMS_API_KEY`
- Update handlers to fetch real data from backend endpoints
- Handle errors gracefully — backend down should produce friendly messages, not crashes
- Implement `/health` (backend status), `/labs` (list labs), `/scores <lab>` (per-task pass rates)

**Why this matters:** Users need real data, not placeholders. Proper error handling ensures the bot remains usable even when the backend is unavailable.

## Task 3: Intent-Based Natural Language Routing

**Goal:** Enable plain text questions interpreted by an LLM.

**Approach:**
- Create an LLM client in `services/llm_client.py`
- Wrap all 9 backend endpoints as LLM tools with clear descriptions
- Build an intent router that sends user text to the LLM, which decides which tool to call
- The LLM receives tool descriptions and returns structured tool calls
- Execute the requested tool and return results to the user

**Why this matters:** Users can ask questions naturally ("what labs are available?") instead of memorizing slash commands. The LLM's tool-calling ability handles routing based on intent.

## Task 4: Containerize and Deploy

**Goal:** Deploy the bot alongside the backend on the VM.

**Approach:**
- Create a `Dockerfile` for the bot
- Add the bot as a service in `docker-compose.yml`
- Configure Docker networking so the bot can reach the backend using service names (not `localhost`)
- Document deployment steps in README
- Verify the bot responds in Telegram after deployment

**Why this matters:** Containerization ensures consistent deployment. Docker Compose orchestrates all services together. Proper networking lets containers communicate using service names.

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│  User Input (Telegram or --test)                            │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────┐                                        │
│  │  bot.py         │  ← Entry point, Telegram startup       │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  Intent Router  │  ← Routes to handlers or LLM           │
│  └────────┬────────┘                                        │
│           │                                                 │
│     ┌─────┴─────┐                                           │
│     │           │                                           │
│     ▼           ▼                                           │
│  ┌─────────┐ ┌──────────┐                                   │
│  │Handlers │ │ LLM      │                                   │
│  │(slash)  │ │ (tools)  │                                   │
│  └────┬────┘ └─────┬────┘                                   │
│       │            │                                        │
│       └─────┬──────┘                                        │
│             │                                               │
│             ▼                                               │
│  ┌─────────────────┐                                        │
│  │  API Client     │  ← HTTP calls to backend               │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  LMS Backend    │                                        │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

1. **Handler separation:** Handlers don't import Telegram libraries. This makes them testable and reusable.
2. **Environment variables:** All secrets (tokens, API keys) come from `.env.bot.secret`, loaded via `config.py`.
3. **LLM tool routing:** The LLM decides which tool to call based on descriptions — no regex or keyword matching in code.
4. **Docker networking:** Containers use service names (e.g., `backend`) instead of `localhost` for internal communication.
