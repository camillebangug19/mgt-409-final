"""Model setup: gpt-6-luna through Portkey, wired into PydanticAI.

Adapted from the course homework pattern in `Lecture 3/test_luna.py`, which
routes the OpenAI client at Portkey and sets the Portkey headers. The key is
read from .env by config.get_portkey_api_key() and is never logged.

Note: this uses OpenAIResponsesModel, not OpenAIChatModel. gpt-6-luna rejects
function tools on /v1/chat/completions ("Function tools with reasoning_effort
are not supported ... use /v1/responses"), and every agent here uses tools.
"""

from functools import lru_cache

from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import MODEL_NAME, PORTKEY_BASE_URL, get_portkey_api_key


@lru_cache(maxsize=1)
def get_model() -> OpenAIResponsesModel:
    """The one model every agent uses. Cached so the client is reused."""
    portkey_api_key = get_portkey_api_key()

    client = AsyncOpenAI(
        api_key=portkey_api_key,
        base_url=PORTKEY_BASE_URL,
        default_headers={
            "x-portkey-api-key": portkey_api_key,
            "x-portkey-provider": "openai",
        },
    )
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
