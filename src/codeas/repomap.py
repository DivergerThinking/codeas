import logging
import os
from collections import Counter, defaultdict, namedtuple
from pathlib import Path

import networkx as nx
import pkg_resources
import tiktoken
from grep_ast import TreeContext, filename_to_lang
from pygments.lexers import guess_lexer_for_filename
from pygments.token import Token
from pygments.util import ClassNotFound
from tree_sitter_languages import get_language, get_parser

Tag = namedtuple("Tag", "rel_fname fname line name kind".split())


def read_text(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


class RepoMap:
    def __init__(
        self,
        max_map_tokens=1024,
        root=os.getcwd(),
        model="gpt-3.5-turbo-1106",
        verbose=False,
    ):
        self.max_map_tokens = max_map_tokens
        self.root = root
        self.tokenizer = tiktoken.encoding_for_model(model)
        self.verbose = verbose

    def get_repo_map(self, chat_files, other_files):
        if self.max_map_tokens <= 0:
            logging.warning("Max map tokens should be positive")
            return

        if not other_files:
            logging.warning("No files passed")
            return

        files_listing = self.get_ranked_tags_map(chat_files, other_files)
        if not files_listing:
            logging.warning("No files remaining after ranking tags")
            return

        if self.verbose:
            logging.info(
                f"Repo-map: {self.token_count(files_listing)/1024:.1f} k-tokens"
            )

        return files_listing

    def token_count(self, string):
        return len(self.tokenizer.encode(string))

    def get_rel_fname(self, fname):
        return os.path.relpath(fname, self.root)

    def get_tags(self, fname, rel_fname):
        return list(self.get_tags_raw(fname, rel_fname))

    def get_tags_raw(self, fname, rel_fname):
        lang = filename_to_lang(fname)
        if not lang:
            return

        language = get_language(lang)
        parser = get_parser(lang)

        # Load the tags queries
        scm_fname = pkg_resources.resource_filename(
            __name__, os.path.join("queries", f"tree-sitter-{lang}-tags.scm")
        )
        query_scm = Path(scm_fname)
        if not query_scm.exists():
            return
        query_scm = query_scm.read_text()

        code = read_text(fname)
        if not code:
            return
        tree = parser.parse(bytes(code, "utf-8"))

        # Run the tags queries
        query = language.query(query_scm)
        captures = query.captures(tree.root_node)

        captures = list(captures)

        saw = set()
        for node, tag in captures:
            if tag.startswith("name.definition."):
                kind = "def"
            elif tag.startswith("name.reference."):
                kind = "ref"
            else:
                continue

            saw.add(kind)

            result = Tag(
                rel_fname=rel_fname,
                fname=fname,
                name=node.text.decode("utf-8"),
                kind=kind,
                line=node.start_point[0],
            )

            yield result

        if "ref" in saw:
            return
        if "def" not in saw:
            return

        # We saw defs, without any refs
        # Some tags files only provide defs (cpp, for example)
        # Use pygments to backfill refs

        try:
            lexer = guess_lexer_for_filename(fname, code)
        except ClassNotFound:
            return

        tokens = list(lexer.get_tokens(code))
        tokens = [token[1] for token in tokens if token[0] in Token.Name]

        for token in tokens:
            yield Tag(
                rel_fname=rel_fname,
                fname=fname,
                name=token,
                kind="ref",
                line=-1,
            )

    def get_ranked_tags(self, chat_fnames, other_fnames):
        defines = defaultdict(set)
        references = defaultdict(list)
        definitions = defaultdict(set)

        personalization = dict()

        fnames = set(chat_fnames).union(set(other_fnames))
        chat_rel_fnames = set()

        fnames = sorted(fnames)

        for fname in fnames:
            if not Path(fname).is_file():
                if Path(fname).exists():
                    logging.warning(
                        f"Repo-map can't include {fname}, it is not a normal file"
                    )
                else:
                    logging.warning(
                        f"Repo-map can't include {fname}, it no longer exists"
                    )
                continue

            # dump(fname)
            rel_fname = self.get_rel_fname(fname)

            if fname in chat_fnames:
                personalization[rel_fname] = 1.0
                chat_rel_fnames.add(rel_fname)

            tags = list(self.get_tags(fname, rel_fname))
            if tags is None:
                continue

            for tag in tags:
                if tag.kind == "def":
                    defines[tag.name].add(rel_fname)
                    key = (rel_fname, tag.name)
                    definitions[key].add(tag)

                if tag.kind == "ref":
                    references[tag.name].append(rel_fname)

        if not references:
            references = dict((k, list(v)) for k, v in defines.items())

        idents = set(defines.keys()).intersection(set(references.keys()))

        G = nx.MultiDiGraph()

        for ident in idents:
            definers = defines[ident]
            for referencer, num_refs in Counter(references[ident]).items():
                for definer in definers:
                    G.add_edge(referencer, definer, weight=num_refs, ident=ident)

        if not references:
            pass

        if personalization:
            pers_args = dict(personalization=personalization, dangling=personalization)
        else:
            pers_args = dict()

        try:
            ranked = nx.pagerank(G, weight="weight", **pers_args)
        except ZeroDivisionError:
            return []

        # distribute the rank from each source node, across all of its out edges
        ranked_definitions = defaultdict(float)
        for src in G.nodes:
            src_rank = ranked[src]
            total_weight = sum(
                data["weight"] for _src, _dst, data in G.out_edges(src, data=True)
            )
            for _src, dst, data in G.out_edges(src, data=True):
                data["rank"] = src_rank * data["weight"] / total_weight
                ident = data["ident"]
                ranked_definitions[(dst, ident)] += data["rank"]

        ranked_tags = []
        ranked_definitions = sorted(
            ranked_definitions.items(), reverse=True, key=lambda x: x[1]
        )

        for (fname, ident), rank in ranked_definitions:
            if fname in chat_rel_fnames:
                continue
            ranked_tags += list(definitions.get((fname, ident), []))

        rel_other_fnames_without_tags = set(
            self.get_rel_fname(fname) for fname in other_fnames
        )

        fnames_already_included = set(rt[0] for rt in ranked_tags)

        top_rank = sorted(
            [(rank, node) for (node, rank) in ranked.items()], reverse=True
        )
        for rank, fname in top_rank:
            if fname in rel_other_fnames_without_tags:
                rel_other_fnames_without_tags.remove(fname)
            if fname not in fnames_already_included:
                ranked_tags.append((fname,))

        for fname in rel_other_fnames_without_tags:
            ranked_tags.append((fname,))

        return ranked_tags

    def get_ranked_tags_map(self, chat_fnames, other_fnames=None):
        if not other_fnames:
            other_fnames = list()

        ranked_tags = self.get_ranked_tags(chat_fnames, other_fnames)
        num_tags = len(ranked_tags)

        lower_bound = 0
        upper_bound = num_tags
        best_tree = None

        chat_rel_fnames = [self.get_rel_fname(fname) for fname in chat_fnames]

        while lower_bound <= upper_bound:
            middle = (lower_bound + upper_bound) // 2
            tree = self.to_tree(ranked_tags[:middle], chat_rel_fnames)
            num_tokens = self.token_count(tree)

            if num_tokens < self.max_map_tokens:
                best_tree = tree
                lower_bound = middle + 1
            else:
                upper_bound = middle - 1

        return best_tree

    def to_tree(self, tags, chat_rel_fnames):
        if not tags:
            return ""

        tags = [tag for tag in tags if tag[0] not in chat_rel_fnames]
        tags = sorted(tags)

        cur_fname = None
        context = None
        output = ""

        # add a bogus tag at the end so we trip the this_fname != cur_fname...
        dummy_tag = (None,)
        for tag in tags + [dummy_tag]:
            this_rel_fname = tag[0]

            # ... here ... to output the final real entry in the list
            if this_rel_fname != cur_fname:
                if context:
                    context.add_context()
                    output += "\n"
                    output += cur_fname + ":\n"
                    output += context.format()
                    context = None
                elif cur_fname:
                    output += "\n" + cur_fname + "\n"

                if type(tag) is Tag:
                    code = read_text(tag.fname) or ""

                    context = TreeContext(
                        tag.rel_fname,
                        code,
                        color=False,
                        line_number=False,
                        child_context=False,
                        last_line=False,
                        margin=0,
                        mark_lois=False,
                        loi_pad=0,
                        # header_max=30,
                        show_top_of_file_parent_scope=False,
                    )
                cur_fname = this_rel_fname

            if context:
                context.add_lines_of_interest([tag.line])

        return output


if __name__ == "__main__":
    chat_fnames = []
    other_fnames = [
        os.path.join("src/codeas", f)
        for f in os.listdir("src/codeas")
        if not f.startswith("__")
    ]

    rm = RepoMap()
    repo_map = rm.get_repo_map(chat_fnames, other_fnames)
    print(repo_map)
