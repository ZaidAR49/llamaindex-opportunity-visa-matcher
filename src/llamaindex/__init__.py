"""LlamaIndex Opportunity & Visa Matcher package."""

def main() -> None:
    """Entry point dispatch function."""
    from llamaindex.main import main as run_app
    run_app()

__all__ = ["main"]
