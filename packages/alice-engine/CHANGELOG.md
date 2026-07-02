# Changelog

## 0.1.0 (2026-07-01)

Initial release.

### Features

- `Engine` class with sync `run()` and async `run_async()` APIs
- `RunResult` dataclass with typed fields and `success` property
- `EventBus` for pub/sub event handling
- `EngineExtension` protocol for lifecycle hooks
- `MockProvider` for testing without real LLM calls
- `ProjectConfig` for project configuration loading
- `ValidationResult` for project validation
- Custom exception hierarchy (`AliceError`, `ConfigError`, etc.)
- Provider registry with lazy loading for optional dependencies

### Dependencies

- Core: langgraph, pyyaml, python-dotenv, pydantic
- Optional: anthropic, openai, typer, rich
