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


def format_gemini_error(error: Exception, step_name: str, model: str = "") -> str:
    """Format a Gemini API error as a structured block."""
    error_str = str(error)
    error_type = type(error).__name__

    if "UNAUTHENTICATED" in error_str or "API_KEY_INVALID" in error_str or "InvalidApiKey" in error_type:
        return (
            "\n"
            "============================================================\n"
            f"  GEMINI API ERROR in {step_name} -- Authentication Failed\n"
            "============================================================\n"
            "\n"
            "  Your Google AI API key was rejected.\n"
            "\n"
            "  --- Fix it ---\n"
            "  1. Check your key at https://aistudio.google.com/apikey\n"
            "  2. Make sure the key is active\n"
            "  3. The Gemini API is free for low usage -- no billing setup needed\n"
            "\n"
            "  Copy this entire block and paste it to an AI assistant for help.\n"
            "============================================================\n"
        )
    elif "RESOURCE_EXHAUSTED" in error_str or "429" in error_str or "quota" in error_str.lower():
        return (
            "\n"
            "============================================================\n"
            f"  GEMINI API ERROR in {step_name} -- Rate Limited\n"
            "============================================================\n"
            "\n"
            "  Too many requests to the Gemini API.\n"
            "  Free tier: 5-15 requests/minute depending on model.\n"
            "  Wait a minute and try again, or switch to a paid plan.\n"
            "\n"
            "  Copy this entire block and paste it to an AI assistant for help.\n"
            "============================================================\n"
        )
    else:
        return (
            "\n"
            "============================================================\n"
            f"  GEMINI API ERROR in {step_name}\n"
            "============================================================\n"
            "\n"
            f"  Error type: {error_type}\n"
            f"  Error: {error}\n"
            f"  Model: {model}\n"
            "\n"
            "  --- Fix it ---\n"
            "  1. Check Google AI status: https://status.cloud.google.com\n"
            "  2. Verify your API key at https://aistudio.google.com/apikey\n"
            f"  3. Confirm model '{model}' is available\n"
            "\n"
            "  Copy this entire block and paste it to an AI assistant for help.\n"
            "============================================================\n"
        )
