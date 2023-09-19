from abc import ABC, abstractmethod
from pydantic import BaseModel

from divergen.codebase_manager import CodebaseManager 

class Retriever(ABC, BaseModel):
    @abstractmethod
    def retrieve(self, **user_input) -> dict:
        pass

class CodeRetriever(Retriever, CodebaseManager):
    def retrieve(self, **user_input):
        self.parse_modules()
        if user_input.get("entity_name") is not None:
            entity_name = user_input.pop("entity_name")
            if user_input.get("module_name") is not None:
                module_name = user_input.pop("module_name")
                code = self.get_entity_source_code(entity_name, module_name)
            else:
                code = self.get_entity_source_code(entity_name)
        elif user_input.get("module_name") is not None:
            module_name = user_input.pop("module_name") 
            code = self.get_module_source_code(module_name)
        else:
            raise ValueError("Either entity_name or module_name must be provided to CodeRetriver")
        user_input.update({"code":code})
        return user_input