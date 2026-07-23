from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel
from app.core.config import settings

def get_llm_provider(temperature: float = 0.0) -> BaseChatModel:
    """
    Returns an initialized LangChain ChatModel based on the application configuration.
    Currently supports Gemini. This abstraction allows easily swapping in OpenAI/Anthropic in the future.
    """
    if settings.LLM_PROVIDER.lower() == "gemini":
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            api_key = "dummy-key-for-testing"
        
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=api_key,
            temperature=temperature,
            convert_system_message_to_human=True # Required for some older Gemini models in LangChain
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
