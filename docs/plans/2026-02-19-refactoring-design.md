# Design Document: Full Project Refactoring

## Overview
This document outlines the architectural changes for the Gemini project, moving from a monolithic Streamlit application to a modular, service-oriented architecture.

## Goals
- **Maintainability**: Smaller, focused files.
- **Testability**: Isolated business logic for unit testing.
- **Scalability**: Easier to add new features or switch API versions.
- **Security**: Centralized configuration and secret management.

## Architecture: Component-Based Dispatcher
We will use a component-based approach with a thin `app.py` dispatcher and a clear separation of concerns.

### 1. Structure
```
gemini/
├── app.py                # Thin entry point (Tabs/Navigation)
├── components/           # Streamlit UI components
│   ├── image_generator.py
│   ├── deep_research.py
│   └── gemini_chat.py
├── services/             # Business logic and API wrappers
│   ├── gemini_client.py  # Shared Gemini client
│   ├── image_service.py
│   ├── research_service.py
│   ├── chat_service.py
│   └── telegram_service.py
├── config/               # Centralized configuration
│   ├── settings.py       # Env vars and app settings
│   ├── styles.py         # UI CSS styles
│   └── prompts.py        # Shared prompt templates
├── utils/                # General utilities
│   ├── file_utils.py
│   └── session_state.py
└── tests/                # Automated tests (Pytest)
```

### 2. Service Layer
The service layer will encapsulate all API interactions and data processing. UI components will only call methods on these services.
- **Gemini Client**: A singleton-like wrapper for the `google-genai` library.
- **Telegram Service**: A proper async implementation for logging and notifications.

### 3. Configuration Management
All hardcoded values, CSS, and prompt templates will be moved to the `config/` directory. Sensitive information (API keys, chat IDs) will be loaded from environment variables using a `.env` file (not committed).

### 4. Testing Strategy
- **Unit Tests**: Test services in isolation using mocks for external APIs (Gemini, Telegram).
- **Integration Tests**: Verify the interaction between services and configuration.

## Success Criteria
- `app.py` is under 100 lines.
- All core logic is covered by unit tests.
- Application functionality remains identical for the end user.
- Zero hardcoded secrets in the codebase.
