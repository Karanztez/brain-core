"""Adapter from MultiProviderRouter to the cognitive model port."""
from brain_core.cognition.contracts import ModelRequest
from brain_core.providers.router import MultiProviderRouter


class RouterModelGateway:
    def __init__(self, router: MultiProviderRouter) -> None:
        self.router = router

    async def generate(self, request: ModelRequest) -> str:
        result = await self.router.chat_completion(
            messages=[{"role": message.role, "content": message.content} for message in request.messages],
            model_override=request.decision.model_override,
            model_tier=request.decision.model_tier,
        )
        if result is None:
            raise RuntimeError("no model provider succeeded")
        return result
