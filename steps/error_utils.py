"""
Shared error formatting for the Market Entry Radar pipeline.

All step files use these helpers to produce structured, copy-pasteable
error messages that a non-developer can paste into an LLM for help.
"""


def format_claude_error(error: Exception, step_name: str, model: str = "") -> str:
    """Format a Claude API error as a structured block."""
    error_type = type(error).__name__

    if "AuthenticationError" in error_type:
        return (
            "\n"
            "============================================================\n"
            f"  CLAUDE API ERROR in {step_name} -- Authentication Failed\n"
            "============================================================\n"
            "\n"
            "  Your Anthropic API key was rejected.\n"
            "\n"
            "  --- Fix it ---\n"
            "  1. Check your key at https://console.anthropic.com/settings/keys\n"
            "  2. Make sure the key is active and has available credits\n"
            "  3. The key should start with 'sk-ant-'\n"
            "\n"
            "  Copy this entire block and paste it to an AI assistant for help.\n"
            "============================================================\n"
        )
    elif "RateLimitError" in error_type:
        return (
            "\n"
            "============================================================\n"
            f"  CLAUDE API ERROR in {step_name} -- Rate Limited\n"
            "============================================================\n"
            "\n"
            "  Too many requests to the Anthropic API.\n"
            "  Wait a few minutes and try again, or reduce max_competitors.\n"
            "\n"
            "  Copy this entire block and paste it to an AI assistant for help.\n"
            "============================================================\n"
        )
    else:
        return (
            "\n"
            "============================================================\n"
            f"  CLAUDE API ERROR in {step_name}\n"
            "============================================================\n"
            "\n"
            f"  Error type: {error_type}\n"
            f"  Error: {error}\n"
            f"  Model: {model}\n"
            "\n"
            "  --- Fix it ---\n"
            "  1. Check Anthropic status: https://status.anthropic.com\n"
            "  2. Verify your API key has credits remaining\n"
            f"  3. Confirm model '{model}' is available on your plan\n"
            "\n"
            "  Copy this entire block and paste it to an AI assistant for help.\n"
            "============================================================\n"
        )
