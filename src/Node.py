from typing import ForwardRef, List

from pydantic.main import BaseModel

from src.DB import get_db_content

Node = ForwardRef('Node')


class Node(BaseModel):
    name: str = ''
    children: List[str] = []  # not Node, otherwise maximum recursion due to self-referencing
    parents: List[Node] = []
    pagerank: float = 1.0


    @classmethod
    def fetch(cls, name: str) -> "Node":
        db_result = get_db_content(name)
        if db_result:
            # https://treyhunner.com/2018/10/asterisks-in-python-what-they-are-and-how-to-use-them/
            return cls(**db_result)
        node = cls()
        node.name = name
        return node

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
