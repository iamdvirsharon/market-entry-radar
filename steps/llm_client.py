"""
LLM client abstraction layer.

Supports:
1. Claude (Anthropic) -- default
2. Gemini (Google) -- alternative, has a free tier

All step files call call_llm() instead of provider-specific APIs.
"""

from rich.console import Console

console = Console()

# Default models per provider
DEFAULT_MODELS = {
    "claude": "claude-sonnet-4-20250514",
    "gemini": "gemini-2.5-flash",
}

# Fast/cheap models for simple tasks (e.g., Step 0 product detection)
FAST_MODELS = {
    "claude": "claude-haiku-4-5-20251001",
    "gemini": "gemini-2.0-flash",
}


def get_fast_model(env: dict) -> str:
    """Get the fastest/cheapest model for the configured provider."""
    provider = env.get("LLM_PROVIDER", "claude")
    return FAST_MODELS.get(provider, FAST_MODELS["claude"])


def call_llm(
    env: dict,
    system_prompt: str,
    user_content: str,
    max_tokens: int = 8192,
    model_override: str = None,
    step_name: str = "",
) -> str:
    """
    Make an LLM call using the configured provider.

    Args:
        env: Environment dict with LLM_PROVIDER, LLM_API_KEY, LLM_MODEL
        system_prompt: System instruction
        user_content: User message content
        max_tokens: Max response tokens
        model_override: Override the default model (e.g., for Step 0 using Haiku)
        step_name: For error messages (e.g., "Step 3: ANALYZE")

    Returns:
        str: The LLM response text
    """
    provider = env.get("LLM_PROVIDER", "claude")
    api_key = env.get("LLM_API_KEY") or env.get("ANTHROPIC_API_KEY", "")
    model = model_override or env.get("LLM_MODEL", DEFAULT_MODELS.get(provider, ""))

    if not api_key:
        raise RuntimeError(
            "\n"
            "============================================================\n"
            f"  LLM API KEY MISSING -- {step_name}\n"
            "============================================================\n"
            "\n"
            f"  Provider: {provider}\n"
            "  No API key found.\n"
            "\n"
            "  --- Fix it ---\n"
            f"  Set your {'Anthropic' if provider == 'claude' else 'Google AI'} API key.\n"
            "\n"
            "  Copy this entire block and paste it to an AI assistant for help.\n"
            "============================================================\n"
        )

    if provider == "gemini":
        return _call_gemini(api_key, model, system_prompt, user_content, max_tokens, step_name)
    else:
        return _call_claude(api_key, model, system_prompt, user_content, max_tokens, step_name)


def _call_claude(api_key: str, model: str, system_prompt: str,
                 user_content: str, max_tokens: int, step_name: str) -> str:
    """Call Anthropic Claude API."""
    import anthropic
    from anthropic import Anthropic
    from steps.error_utils import format_claude_error

    try:
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        return response.content[0].text
    except (anthropic.AuthenticationError, anthropic.RateLimitError, anthropic.APIError) as e:
        raise RuntimeError(format_claude_error(e, step_name, model)) from e


def _call_gemini(api_key: str, model: str, system_prompt: str,
                 user_content: str, max_tokens: int, step_name: str) -> str:
    """Call Google Gemini API."""
    from steps.error_utils import format_gemini_error

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text
    except Exception as e:
        raise RuntimeError(format_gemini_error(e, step_name, model)) from e
