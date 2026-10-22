# Contributing to AOG

## Development Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd agent-observability-graph
   ```

2. Install dependencies:
   ```bash
   make install
   ```

3. Start the development environment:
   ```bash
   make dev
   ```

4. Run tests:
   ```bash
   make test
   ```

## Development Workflow

### Making Changes

1. Write tests for your feature
2. Implement the feature
3. Run tests, lint, and typecheck
4. Update documentation
5. Open a pull request

### Commands

```bash
make install    # Install dependencies
make dev        # Start docker-compose
make test       # Run all tests
make lint       # Run linter
make typecheck  # Run type checker
make format     # Format code
make clean      # Clean temporary files
```

## Code Style

- Use `ruff` for formatting and linting
- Follow PEP 8 conventions
- Use type hints everywhere
- Keep functions under 300 lines
- Write docstrings for public APIs

## Testing

### Running Tests

```bash
# All tests
make test

# Unit tests only
uv run pytest tests/unit/

# Integration tests
uv run pytest tests/integration/

# With coverage
uv run pytest --cov
```

### Writing Tests

1. Unit tests go in `tests/unit/`
2. Integration tests go in `tests/integration/`
3. E2E tests go in `tests/e2e/`
4. Fixtures go in `tests/fixtures/`

Use descriptive test names and clear assertions.

## Integration Development

When adding a new integration:

1. Create a new directory under `integrations/`
2. Map framework events to `AgentEvent`
3. Follow privacy and redaction rules
4. Write unit and integration tests
5. Document the integration

## Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run all checks
5. Open a pull request

## Questions?

Open an issue or reach out to the maintainers.