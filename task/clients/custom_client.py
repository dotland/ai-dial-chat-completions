import json
import aiohttp
import requests

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class CustomDialClient(BaseClient):
    """
    A manual implementation of the DIAL client using `requests` and `aiohttp`.

    This mirrors what the SDK does, but keeps everything explicit so that it is
    easy to follow for learning purposes.
    """

    _endpoint: str

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        self._endpoint = (
            f"{DIAL_ENDPOINT}/openai/deployments/{deployment_name}/chat/completions"
        )

    def get_completion(self, messages: list[Message]) -> Message:
        """
        Send synchronous request to DIAL API and return AI response.
        """
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json",
        }

        request_data = {
            "messages": [msg.to_dict() for msg in messages],
        }

        response = requests.post(
            self._endpoint,
            headers=headers,
            json=request_data,
        )

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("No Choice has been present in the response")

        first_choice = choices[0]
        message_obj = first_choice.get("message") or {}
        content = message_obj.get("content", "")

        print(content)
        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        """
        Send asynchronous streaming request to DIAL API and return AI response.
        """
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json",
        }

        request_data = {
            "stream": True,
            "messages": [msg.to_dict() for msg in messages],
        }

        contents: list[str] = []

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self._endpoint,
                headers=headers,
                json=request_data,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"{response.status} {error_text}")
                    return Message(role=Role.AI, content="")

                async for line in response.content:
                    line_str = line.decode("utf-8").strip()
                    if not line_str.startswith("data: "):
                        continue

                    data = line_str[6:].strip()
                    if data == "[DONE]":
                        # End of stream – break the loop and move to next line.
                        print()
                        break

                    content_snippet = self._get_content_snippet(data)
                    if content_snippet:
                        print(content_snippet, end="")
                        contents.append(content_snippet)

        return Message(role=Role.AI, content="".join(contents))

    def _get_content_snippet(self, data: str) -> str:
        """
        Extract content from one streaming data chunk.
        """
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            return ""

        choices = parsed.get("choices") or []
        if not choices:
            return ""

        delta = choices[0].get("delta") or {}
        return delta.get("content", "") or ""
