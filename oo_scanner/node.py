"""Tree Node definition"""

import ast


class Node:
    """Wrapper of node object in ast tree."""

    def __init__(
        self,
        node,
        parent=None,
        children=None,
        parent_child_re=None,
    ):
        self.node = node
        self.parent = parent
        self.children = children
        self.parent_child_re = parent_child_re
        self.type = type(node)

    def __repr__(self):
        try:
            return f"{self.type} from line {self.node.lineno} to line {self.node.end_lineno}"
        except Exception as e:
            return self.node.__repr__()

    def find_parent_of_type(self, target_type) -> None | "Node":
        """Find the parent of a certain type by moving up the tree."""
        current = self.parent
        while current:
            if isinstance(current.node, target_type):
                return current
            current = current.parent
        return None

    def get_enclosing_function(self) -> None | str:
        """Get the enclosing function node by moving up the tree."""
        enclosing_func = self.find_parent_of_type(ast.FunctionDef)

        if enclosing_func:
            return enclosing_func.node.name
        return None

    def get_enclosing_class(self) -> None | str:
        """Get the enclosing class node by moving up the tree."""
        enclosing_class = self.find_parent_of_type(ast.ClassDef)

        if enclosing_class:
            return enclosing_class.node.name
        return None

    def get_enclosing_module(self):
        """Get the enclosing module node by moving up the tree."""
        enclosing_module = self.find_parent_of_type(ast.Module)
        if enclosing_module:
            return enclosing_module.module_path
        return None


class ModuleNode(Node):
    """Represent the module level node."""

    def __init__(
        self, node, parent=None, children=None, parent_child_re=None, module_path=None
    ):
        super().__init__(node, parent, children, parent_child_re)
        self.module_path = module_path
