"""The server-owned catalog of chat models and their credentials."""

from dataclasses import asdict, dataclass

from django.conf import settings


@dataclass(frozen=True)
class ChatModel:
    """One supported model, identified by the stable id exposed to clients."""

    id: str
    api_model: str
    label: str
    provider: str

    def public(self):
        """Return only metadata that is safe to send to a browser."""
        return {key: value for key, value in asdict(self).items() if key != "api_model"}


class ChatModelUnavailable(Exception):
    """The requested model is not enabled by this server's configuration."""


class ChatNotConfigured(Exception):
    """No configured provider can serve chat requests."""


def available_models():
    """Return the curated models whose corresponding backend credentials exist."""
    models = []
    if settings.ANTHROPIC_API_KEY:
        models.append(
            ChatModel(
                id=f"anthropic/{settings.ANTHROPIC_CHAT_DEFAULT_MODEL}",
                api_model=settings.ANTHROPIC_CHAT_DEFAULT_MODEL,
                label=settings.ANTHROPIC_CHAT_DEFAULT_MODEL.replace("-", " ").title(),
                provider="Anthropic",
            )
        )
    if settings.OPENCODE_GO_API_KEY:
        models.extend(
            ChatModel(
                id=model_id,
                api_model=api_model,
                label=label,
                provider="OpenCode Go",
            )
            for model_id, api_model, label in settings.OPENCODE_GO_MODELS
        )
    return models


def default_model(models=None):
    """Choose the configured default, falling back predictably when it is unavailable."""
    models = models if models is not None else available_models()
    if not models:
        raise ChatNotConfigured("The course chat assistant is not configured on this server.")

    configured_id = settings.CHAT_DEFAULT_MODEL
    for model in models:
        if model.id == configured_id:
            return model

    return models[0]


def resolve_model(model_id=None):
    """Resolve a client model id without accepting arbitrary providers or endpoints."""
    models = available_models()
    if not models:
        raise ChatNotConfigured("The course chat assistant is not configured on this server.")
    if not model_id:
        return default_model(models)
    for model in models:
        if model.id == model_id:
            return model
    raise ChatModelUnavailable("That chat model is not available on this server.")


def model_catalog():
    """The complete, key-gated catalog used by the frontend model selector."""
    models = available_models()
    return {
        "default_model": default_model(models).id if models else None,
        "models": [model.public() for model in models],
    }
