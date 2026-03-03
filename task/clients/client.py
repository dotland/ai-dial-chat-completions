from aidial_client import Dial, AsyncDial

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class DialClient(BaseClient):

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        # Documentation: https://pypi.org/project/aidial-client/
        # Synchronous client – used for regular (non‑streaming) calls.
        self._client = Dial(
            base_url=DIAL_ENDPOINT,
            api_key=self._api_key,
        )
        # Asynchronous client – used for streaming calls.
        self._async_client = AsyncDial(
            base_url=DIAL_ENDPOINT,
            api_key=self._api_key,
        )

    def get_completion(self, messages: list[Message]) -> Message:
        """
        Send a regular (non‑streaming) request using the aidial-client SDK.
        """
        response = self._client.chat.completions.create(
            deployment_name=self._deployment_name,
            messages=[msg.to_dict() for msg in messages],
        )

        choices = getattr(response, "choices", None)
        if not choices:
            raise Exception("No choices in response found")

        first_choice = choices[0]
        message_obj = getattr(first_choice, "message", None)
        if message_obj is None:
            raise Exception("No message in first choice found")

        content = getattr(message_obj, "content", "")
        print(content)
        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        """
        Send a streaming request using the asynchronous aidial-client SDK.
        """
        chunks = await self._async_client.chat.completions.create(
            deployment_name=self._deployment_name,
            messages=[msg.to_dict() for msg in messages],
            stream=True,
        )

        contents: list[str] = []

        async for chunk in chunks:
            choices = getattr(chunk, "choices", None)
            if not choices:
                continue

            delta = getattr(choices[0], "delta", None)
            if delta is None:
                continue

            content_piece = getattr(delta, "content", None)
            if content_piece:
                print(content_piece, end="")
                contents.append(content_piece)

        # Move to the next console line after streaming is finished.
        print()
        return Message(role=Role.AI, content="".join(contents))
