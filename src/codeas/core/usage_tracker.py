import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

USAGE_PATH = str(Path.home() / "codeas" / "usage.json")


class UsageTracker:
    def __init__(self, file_path: str = USAGE_PATH):
        self.file_path = file_path
        self.usage_data = self.load_data()

    def load_data(self) -> Dict:
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                if "chat" not in data:
                    data["chat"] = []
                if "generator" not in data:
                    data["generator"] = []
                return data
        except FileNotFoundError:
            return {"chat": [], "generator": []}

    def save_data(self):
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w") as f:
            json.dump(self.usage_data, f, indent=2)

    def record_usage(self, use_case: str, cost: float):
        if use_case not in self.usage_data:
            self.usage_data[use_case] = {"count": 0, "total_cost": 0.0, "history": []}
        self.usage_data[use_case]["count"] += 1
        self.usage_data[use_case]["total_cost"] += cost
        self.usage_data[use_case]["history"].append(
            {"timestamp": datetime.now().isoformat(), "cost": cost}
        )

        self.save_data()

    def get_usage_stats(self) -> Dict[str, Dict]:
        return self.usage_data

    def log_agent_execution(
        self,
        model: str,
        prompt: str,
        cost: Dict,
        conversation_id: str = None,
        using_template: bool = False,
        using_multiple_templates: bool = False,
        using_multiple_models: bool = False,
    ):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "conversation_id": conversation_id,
            "model": model,
            "prompt": prompt,
            "cost": cost,
            "using_template": using_template,
            "using_multiple_templates": using_multiple_templates,
            "using_multiple_models": using_multiple_models,
        }

        self.usage_data["chat"].append(log_entry)
        self.save_data()

    def log_prompt_generator(
        self, model: str, prompt: str, cost: float, generator: str, action: str
    ):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt": prompt,
            "cost": cost,
            "generator": generator,
            "action": action,
        }

        self.usage_data["generator"].append(log_entry)
        self.save_data()


usage_tracker = UsageTracker()
