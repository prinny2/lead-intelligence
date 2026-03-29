# Lead Intelligence - Copilot Instructions

## Project Overview

Lead Intelligence is a Python-based lead qualification system focused on the **Brazilian solar energy market**. The project consists of:

1. **Core Library** (`lead_intelligence/`): A standalone Python toolkit for filtering and qualifying leads with explicit commercial decisions (accept/review/reject) and traceable reasons. No external dependencies required.
2. **FastAPI Application** (`app/`): Optional REST API for web-based lead qualification with authentication, storage, and integration capabilities.

## Tech Stack

- **Language**: Python 3.10+
- **Web Framework**: FastAPI with Uvicorn
- **AI Provider**: Anthropic Claude (NOT OpenAI) - use `ANTHROPIC_API_KEY` environment variable
- **Testing**: pytest with httpx for API tests
- **Deployment**: Docker, Render, Railway, Google Cloud Run
- **Payment Processing**: Stripe
- **Database**: File-based JSONL storage (leads.jsonl)
- **Authentication**: Firebase Admin SDK

## Code Style & Conventions

### General Python Style

- Follow PEP 8 conventions
- Use type hints for all function parameters and return values (Python 3.10+ style with `dict[str, Any]`, `list[str]`)
- Prefer explicit over implicit: use clear variable names and avoid abbreviations
- Use `from __future__ import annotations` for forward references when needed
- Import order: standard library, third-party packages, local imports (separated by blank lines)

### Naming Conventions

- **Functions**: `snake_case` (e.g., `qualify_lead`, `analyze_interest_message`)
- **Classes**: `PascalCase` (e.g., `LeadRequest`, `StoredLead`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_MODEL`, `TIMEOUT_SECONDS`)
- **Private functions**: Prefix with underscore (e.g., `_decide`, `_find_duplicate`)
- **Module names**: `snake_case` (e.g., `scoring_service.py`, `message_analysis.py`)

### Documentation

- Use docstrings for public functions and classes
- Keep docstrings concise but informative
- Use Portuguese for user-facing messages, reasons, and recommendations
- Use English for code, variable names, and technical documentation
- Document return types in docstrings when not obvious from type hints

### Error Handling

- Use explicit error checking rather than broad try-except blocks
- Log errors with context using the logger: `logger.warning("operation_failed error=%s", str(e))`
- Return `None` or empty values on graceful failures rather than raising exceptions in service layers
- Raise `HTTPException` in FastAPI routes with appropriate status codes

## Architecture Patterns

### Core Library Design (`lead_intelligence/`)

- **Zero Dependencies**: The core library has no external dependencies by design
- **Pure Functions**: Prefer stateless functions that take input and return output
- **Explicit Decisions**: Always return structured data with `decision`, `reasons`, and `score`
- **Modular Pipeline**: `validator.py` → `analyzer.py` → `scorer.py` → `qualifier.py`
- **Optional Enhancements**: Use `solar.py` for niche-specific heuristics, `message_analysis.py` for text analysis

### API Design (`app/`)

- **Service Layer**: Business logic lives in `app/services/`, not in routes
- **Routes**: Keep route handlers thin - they should orchestrate services and handle HTTP concerns
- **Models**: Use Pydantic models in `app/models/schemas.py` for request/response validation
- **Authentication**: Use `require_auth` dependency for protected endpoints
- **Multi-tenancy**: Filter data by `org_id` from `ClientInfo`

### AI Service Integration

- **Provider**: Use Anthropic Claude via the `anthropic` package
- **Model**: Default model is `claude-haiku-4-5-20251001` (constant: `DEFAULT_MODEL`)
- **Environment Variable**: `ANTHROPIC_API_KEY` (NOT `OPENAI_API_KEY`)
- **Return Pattern**: AI services return tuples: `(ai_output: dict, context: dict)`
- **Fallback**: Always handle cases where AI service is unavailable or returns invalid data
- **Testing**: Mock AI services to return the expected tuple format `(dict, dict)`

## Testing Guidelines

### Test Organization

- Test files mirror source structure: `tests/test_*.py` for each module
- Use pytest class-based organization: `class TestFunctionName:`
- Integration tests: `test_integration_lead_pipeline.py` for end-to-end flows
- API tests: Use `httpx.AsyncClient` for FastAPI endpoint testing

### Test Conventions

- **Mocking AI Services**: Always return tuples `(ai_output: dict, solar_context: dict)`
- **Assertions**: Use specific assertions (`assert x is True` not `assert x`)
- **Fixtures**: Use pytest fixtures for shared test data
- **Coverage**: Focus on critical business logic paths (validation, scoring, qualification)

### Running Tests

```bash
pytest                                      # Run all tests
pytest tests/test_integration_lead_pipeline.py -v  # Specific test with verbose output
pytest -k "test_validator"                  # Run tests matching pattern
```

## Key Business Rules

### Lead Qualification Decisions

- **reject**: Critically incomplete data, no valid contact channel, or score ≤ 32
- **review**: Intermediate data quality, generic email domain, or exploratory intent
- **accept**: Valid contact, high completeness (≥ 0.67), score ≥ 72, clear intent

### Scoring System

- **Core Score** (0-100): Based on completeness, valid contact channels, and data quality
- **AI Score** (0-10): Claude's assessment of lead quality and urgency
- **Hybrid Score**: Combines core heuristics with AI insights, applies business rules

### Solar-Specific Signals

- **Strong Fit**: Monthly bill ≥ R$ 250, owned property, commercial/residential property type
- **Weak Fit**: Rented property, apartment (unless owned), monthly bill < R$ 150
- **Urgency Indicators**: Words like "urgente", "orçamento", "preciso" in interest message

## Security & Environment

### Environment Variables

- `ANTHROPIC_API_KEY`: Required for AI-powered qualification
- `CORS_ORIGINS`: Comma-separated allowed origins for CORS
- `LEADS_FILE`: Path to leads JSONL storage (use persistent disk in production)
- `STRIPE_SECRET_KEY`: For payment processing
- `FIREBASE_CREDENTIALS_BASE64`: Base64-encoded Firebase service account JSON

### Security Practices

- Never commit `.env` files or secrets
- Validate and sanitize all user inputs in Pydantic models
- Use FastAPI's built-in CORS middleware configuration
- Log security events without exposing sensitive data
- Use Firebase tokens for authentication, verify with `firebase_admin`

## Common Workflows

### Adding a New Route

1. Create route handler in `app/routes/`
2. Define request/response models in `app/models/schemas.py`
3. Implement business logic in `app/services/`
4. Add route to main app in `app/main.py`
5. Add authentication with `Depends(require_auth)` if needed
6. Write integration tests in `tests/test_api.py`

### Modifying Lead Qualification Logic

1. Update core logic in `lead_intelligence/` (validator, scorer, or qualifier)
2. Run unit tests: `pytest tests/test_qualifier.py -v`
3. Update AI service integration in `app/services/scoring_service.py` if needed
4. Run integration test: `pytest tests/test_integration_lead_pipeline.py -v`
5. Verify API endpoint behavior with `pytest tests/test_api.py`

### Deployment

- **Local Development**: `uvicorn app.main:app --reload`
- **Docker**: `docker build -t lead-intelligence . && docker run -e ANTHROPIC_API_KEY=... -p 8000:8000 lead-intelligence`
- **Render/Railway**: Use `Procfile` entry: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Google Cloud Run**: Use `cloudbuild.yaml` and `deploy-cloudrun.sh`

## Key Files Reference

- `lead_intelligence/qualifier.py` - Main qualification logic
- `app/services/ai_service.py` - Anthropic Claude integration
- `app/services/scoring_service.py` - Hybrid scoring with AI + heuristics
- `app/routes/leads.py` - Lead API endpoints
- `app/auth.py` - Firebase authentication
- `pyproject.toml` - Package metadata and dependencies

## Common Pitfalls

- **AI Service**: Remember to return tuples `(dict, dict)`, not just `dict`
- **Environment Variables**: Use `ANTHROPIC_API_KEY`, not `OPENAI_API_KEY`
- **Type Hints**: Use modern Python 3.10+ syntax (`dict[str, Any]` not `Dict[str, Any]`)
- **Logging**: Use `logger.info("event key=%s", value)` format with structured keys
- **Multi-tenancy**: Always filter by `org_id` in API routes that access shared data
- **Testing**: Mock AI services must return the expected tuple format
