import json
from datetime import datetime
from typing import Dict


class UsageTracker:
    def __init__(self, file_path: str = ".codeas/use_cases_usage.json"):
        self.file_path = file_path
        self.usage_data = self.load_data()

    def load_data(self) -> Dict:
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_data(self):
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


usage_tracker = UsageTracker()
