class ts_BaseEntity:
    def __init__(self, node, parser, code: str = "", modified: bool = False) -> None:
        self.node = node
        self.parser = parser
        self.code = code
        self.modified = modified

    def get(self, attr):
        return getattr(self, attr)

    def modify(self, attr, value):
        setattr(self, attr, value)
        self.modified = True
        if attr == "code":
            self.update_node(value)

    def update_node(self, code: str):
        if isinstance(self, ts_Module):
            node = self.parser.parse(bytes(code, "utf8")).root_node
            self.node = node
            self.set_code()
        elif isinstance(self, ts_Entity):
            # TODO: With this node update, all start/end bytes references breaks. To review.
            node = self.parser.parse(bytes(code, "utf8")).root_node
            self.node = node
            self.update_module_node()

    def set_code(self):
        self.code = self.node.text.decode()


class ts_Entity(ts_BaseEntity):
    def __init__(
        self,
        node,
        parser,
        module,
        body_idx,
    ) -> None:
        super().__init__(node, parser, node.text.decode())
        self.module = module
        self.body_idx = body_idx

    # def model_post_init(self) -> None:
    #     self.set_code()

    def update_module_node(self):
        self.module.body[self.body_idx] = self.node
        # TODO: Due to recursive call at modify an entity we're updating module code. To review.
        self.module.merge_entities()


class ts_Module(ts_BaseEntity):
    def __init__(self, name: str, node, parser) -> None:
        super().__init__(node, parser, node.text.decode())
        self.name = name
        # self.node = node
        self.body = [child for child in node.children]
        self._entities: list[ts_Entity] = []

    # def model_post_init(self) -> None:
    #     self.set_code()

    def parse_entities(self):
        # TODO: Right now this is useless, but should be adapted to each language.
        for idx, node in enumerate(self.body):
            if node.type in [
                "package_declaration",
                "line_comment",
                "class_declaration",
                "block_comment",
                "class_declaration",
            ]:
                self._entities.append(
                    ts_Entity(node=node, parser=self.parser, module=self, body_idx=idx)
                )

    def merge_entities(self):
        self.code = "\n".join([child.text.decode() for child in self.body])
