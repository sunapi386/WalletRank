from typing import ForwardRef, List

from pydantic.main import BaseModel

from src.DB import get_db_content, set_db_content

Node = ForwardRef('Node')


class Node(BaseModel):
    name: str = ''
    children: List[str] = []  # not Node, otherwise maximum recursion due to self-referencing
    parents: List[Node] = []
    pagerank: float = 1.0
    domain: str = ''

    @classmethod
    def fetch(cls, name: str, domain: str) -> "Node":
        db_result = get_db_content(name, domain)
        if db_result:
            # https://treyhunner.com/2018/10/asterisks-in-python-what-they-are-and-how-to-use-them/
            node = cls(**db_result)
            return node
        node = cls()
        node.name = name
        node.domain = domain
        return node

    def persist(self):
        self_dict = self.dict()
        self_dict['_id'] = self.name
        set_db_content(self_dict, self.domain)

    def link_child(self, new_child):
        for child in self.children:
            if child == new_child.name:
                return None
        self.children.append(new_child.name)

    def link_parent(self, new_parent):
        for parent in self.parents:
            if parent.name == new_parent.name:
                return None
        self.parents.append(new_parent)

    def update_pagerank(self, d, n):
        in_neighbors = self.parents
        pagerank_sum = sum((node.pagerank / len(node.children)) for node in in_neighbors)
        random_jumping = d / n
        self.pagerank = random_jumping + (1 - d) * pagerank_sum


Node.update_forward_refs()
