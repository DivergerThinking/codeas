import os
from typing import Dict

import pyperclip
from langchain.chains import LLMChain
from langchain.prompts import (ChatPromptTemplate,
                               HumanMessagePromptTemplate, load_prompt)
from langchain.prompts.chat import SystemMessage
from pydantic import BaseModel

from divergen.config import DEFAULT_CONFIGS, PromptConfig


class PromptManager(BaseModel):
    prompt_library: str
    prompt_configs: Dict[str, PromptConfig] = DEFAULT_CONFIGS
    
    def execute_prompt(self, action, **user_input):
        prompt_template = self.build_prompt_template(action)
        chain = LLMChain(
            prompt=prompt_template,
            llm=self.prompt_configs[action].model,
            memory=self.prompt_configs[action].memory
        )
        return chain.run(**user_input)
    
    def build_prompt_template(self, action):
        system_prompt = self._get_system_prompt(action)
        return self._build_prompt_template(system_prompt, action)
        
    def _get_system_prompt(self, action):
        system_prompt_path = os.path.join(
            self.prompt_library, self.prompt_configs[action].system_prompt
        )
        with open(system_prompt_path, "r") as f:
            return f.read()
    
    def _build_prompt_template(self, system_prompt, action):
        prompt_template = load_prompt(
            os.path.join(self.prompt_library, self.prompt_configs[action].user_prompt)
        )
        if system_prompt:
            return ChatPromptTemplate.from_messages(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessagePromptTemplate(prompt=prompt_template),
                ]
            )
        else:
            return HumanMessagePromptTemplate(prompt=prompt_template)
    
    def build_prompt(self, action, **user_input):
        system_prompt = self.get_system_prompt(action)
        retriever = self.prompt_configs[action].retriever
        user_input = retriever.retrieve(**user_input)
        return self._build_prompt(system_prompt, action, **user_input)
    
    def _build_prompt(self, system_prompt, action, **user_input):
        user_prompt_template = load_prompt(
            os.path.join(self.prompt_library, self.prompt_configs[action].user_prompt)
        )
        user_prompt = user_prompt_template.format(**user_input)
        if system_prompt:
            return f"{system_prompt}\n{user_prompt}"
        else:
            return user_prompt

    def copy_prompt(self, action, **user_input):
        prompt = self.build_prompt(action, **user_input)
        pyperclip.copy(prompt)