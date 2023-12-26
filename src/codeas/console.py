from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


class RichConsole:
    def __init__(self):
        self.text = Text()
        self.panel = Panel(self.text, title="OpenAI Response")
        self.console = Console()
        self.live = Live(
            self.panel, console=self.console, refresh_per_second=10, transient=True
        )
        self.live.start()

    def display(self, content):
        if content:
            self.text.append(content)
            self.panel = Panel(self.text, title="OpenAI Response")
            self.live.update(self.panel)

    def end(self):
        self.live.stop()
        self.console.print(self.panel)
