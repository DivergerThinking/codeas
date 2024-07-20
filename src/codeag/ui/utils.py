import os


def search_dirs(path: str):
    """
    search function that returns the directories with starting path "path"
    """
    if "/" in path:
        base_dir, start_next_dir = os.path.split(path)
        try:
            return [
                os.path.join(base_dir, d)
                for d in os.listdir(base_dir)
                if os.path.isdir(os.path.join(base_dir, d))
                and d.startswith(start_next_dir)
            ]
        except Exception:
            return []
    elif path == ".":
        return ["."] + [
            os.path.join(path, d)
            for d in os.listdir(path)
            if os.path.isdir(os.path.join(path, d))
        ]
    elif path == "..":
        return [".."] + [
            os.path.join(path, d)
            for d in os.listdir(path)
            if os.path.isdir(os.path.join(path, d))
        ]
