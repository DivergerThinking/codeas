import string

from codeag.core.retriever import Retriever
from codeag.utils.codebase import Codebase


class Context:
    def __init__(self, repo_path: str):
        codebase = Codebase(base_dir=repo_path)
        self.retriever = Retriever(codebase=codebase)

    def fill(self, prompt):
        placeholders = self.identify_placeholders(prompt)
        if len(placeholders) == 1:
            return self.fill_single_placeholder(prompt, placeholders[0])
        else:
            return self.fill_multiple_placeholders(prompt, placeholders)

    def identify_placeholders(self, prompt):
        formatter = string.Formatter()
        return [
            fname
            for _, fname, _, _ in formatter.parse(prompt)
            if fname and fname.startswith("get_")
        ]

    def fill_single_placeholder(self, prompt, placeholder):
        context = getattr(self.retriever, placeholder)()
        if isinstance(context, dict):
            return {
                context_key: prompt.format(**{placeholder: context_value})
                for context_key, context_value in context.items()
            }
        elif isinstance(context, str):
            return prompt.format(**{placeholder: context})
        else:
            raise ValueError(f"Invalid context type: {type(context)}")

    def fill_multiple_placeholders(self, prompt, placeholders):
        contexts = {
            placeholder: getattr(self.retriever, placeholder)()
            for placeholder in placeholders
        }
        if self.contains_placeholders_with_multiple_values(contexts):
            return self.fill_placeholders_with_multiple_values(prompt, contexts)
        else:
            return prompt.format(**contexts)

    def contains_placeholders_with_multiple_values(self, contexts: dict):
        """Identify prompt placeholders return multiple values, stored as dictionary."""
        return any([isinstance(context, dict) for context in contexts.values()])

    def fill_placeholders_with_multiple_values(self, prompt, contexts):
        """Fill prompt with context containing multiple values"""
        keys = self.get_requests_keys(contexts)
        filled_prompts = {}
        for key in keys:
            placeholder_args = self.get_placeholder_args(contexts, key)
            filled_prompts[key] = prompt.format(**placeholder_args)
        return filled_prompts

    def get_requests_keys(self, contexts: dict):
        keys = []
        for context in contexts.values():
            if isinstance(context, dict):
                keys.extend(context.keys())
        return keys

    def get_placeholder_args(self, contexts, key):
        placeholder_mapping = {}
        for placeholder, context_values in contexts.items():
            if isinstance(context_values, dict):
                placeholder_mapping[placeholder] = context_values[key]
            else:
                placeholder_mapping[placeholder] = context_values
        return placeholder_mapping
