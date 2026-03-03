import asyncio

from task.clients.client import DialClient
from task.clients.custom_client import CustomDialClient
from task.constants import DEFAULT_SYSTEM_PROMPT
from task.models.conversation import Conversation
from task.models.message import Message
from task.models.role import Role


async def start(stream: bool) -> None:
    # 1. Choose deployment (model) name.
    print("Enter deployment name (press Enter for 'gpt-4o'):")
    deployment_name = input("> ").strip() or "gpt-4o"

    # 1.1/1.2. Create clients based on the chosen deployment.
    dial_client = DialClient(deployment_name=deployment_name)
    custom_client = CustomDialClient(deployment_name=deployment_name)

    # Ask which client implementation to use for this run.
    print("\nChoose client implementation:")
    print("1 - SDK client (aidial-client)")
    print("2 - Custom HTTP client (requests/aiohttp)")
    client_choice = input("> ").strip() or "1"

    sync_client: DialClient | CustomDialClient
    if client_choice == "2":
        sync_client = custom_client
        print("Using CustomDialClient.\n")
    else:
        sync_client = dial_client
        print("Using SDK DialClient.\n")

    # 2. Create a conversation object to store history.
    conversation = Conversation()

    # 3. Read system prompt or use default.
    print("Provide System prompt or press 'enter' to continue.")
    system_prompt = input("> ").strip() or DEFAULT_SYSTEM_PROMPT
    system_message = Message(role=Role.SYSTEM, content=system_prompt)
    conversation.add_message(system_message)

    # 4. Main chat loop.
    print("\nType your question or 'exit' to quit.")
    while True:
        user_input = input("> ").strip()

        # 5. Exit condition.
        if user_input.lower() == "exit":
            print("Exiting the chat. Goodbye!")
            break

        # Skip empty messages to keep conversation clean.
        if not user_input:
            continue

        # 6. Add user message to conversation history.
        user_message = Message(role=Role.USER, content=user_input)
        conversation.add_message(user_message)

        # 7. Call either streaming or regular completion.
        messages = conversation.get_messages()
        if stream:
            ai_message = await sync_client.stream_completion(messages)
        else:
            ai_message = sync_client.get_completion(messages)

        # 8. Add AI reply to history for context in next turns.
        conversation.add_message(ai_message)


if __name__ == "__main__":
    asyncio.run(start(True))
