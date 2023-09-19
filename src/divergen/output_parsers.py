class PythonOutputParser:
    def parse(self, output: str):
        return output.replace("```python", "").replace("```", "")