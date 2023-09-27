from pydantic import BaseModel

class SearchMixin(BaseModel):
    def _search_by_path(self, path, entities):
        result = [entity for entity in entities if entity.path == path]
        self._check_search(result, path)
        return result[0]

    def _search_by_name(self, name, entities):
        result = [entity for entity in entities if entity.node.name == name]
        self._check_search(result, name)
        return result[0]

    def _search_by_line(self, line_no):
        ...

    def _check_search(self, result, value):
        if len(result) == 0:
            raise ValueError(f"{value} not found")
        elif len(result) > 1:
            raise ValueError(f"Multiple {value} found ")
        else:
            return result