import logging

logger = logging.getLogger(__name__)


class IdTree(dict):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self["_byname"] = {}
        self["_collections"] = {}

    def recursive_get(self, path):
        logger.debug("RGET %r", path)
        branch = self
        for part in path:
            branch = branch[part]
        return branch

    def path_get(self, path):
        parts = path.split("/")
        try:
            value = self.recursive_get(parts)
        except KeyError:
            jid = self.recursive_get(["_byname"] + parts)
            value = self.recursive_get(parts[:-1] + [jid])
        if path in self["_collections"]:
            return list(value.values())
        return value

    def path_set(self, path, value):
        parts = path.split("/")
        return self.recursive_set(parts, value)

    def get_branch(self, path):
        branch = self
        for part in path:
            try:
                sub = branch[part]
            except KeyError:
                sub = branch[part] = {}
            branch = sub
        return branch

    def recursive_set(self, path, value):
        branch = self.get_branch(path[:-1])
        branch[path[-1]] = value

    def add_collection(self, path, items, key="name", id_key="id"):
        parts = path.split("/")
        branch = self.get_branch(parts)
        names_branch = self.get_branch(["_byname"] + parts)
        self["_collections"][path] = key
        for item in items:
            jid = item[id_key]
            name = item[key]
            branch[jid] = item
            names_branch[name] = jid

    def new_element(self, path, item, key="name", id_key="id", min_id=100_000):
        if path not in self["_collections"]:
            self["_collections"][path] = key
        parts = path.split("/")
        branch = self.get_branch(parts)
        names_branch = self.get_branch(["_byname"] + parts)
        if id_key == "id" and "id" not in item:
            for num_jid in range(min_id, 1_000_000):
                jid = str(num_jid)
                if jid not in branch:
                    break
            item[id_key] = jid
            item["self"] = item["self"].replace("{JID}", jid)
        else:
            jid = item[id_key]
        branch[jid] = item
        name = item[key]
        names_branch[name] = jid
