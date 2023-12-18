from codeas.chat import Chat


def start_terminal():
    chat = Chat()
    while True:
        try:
            message = input("> ").strip()
        except KeyboardInterrupt:
            break

        if isinstance(message, str):
            chat.ask(message)
