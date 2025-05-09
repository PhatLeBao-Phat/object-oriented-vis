import ast
from typing import List, Union
import re
from pathlib import Path
import os

from oo_scanner.node import Node, ModuleNode


class ModuleTree:
    """Responsible for managing tree interior nodes and tree-related methods at module level."""

    def __init__(self, root: Node = None, module_path: str = None) -> None:
        """
        Initialize the Tree object.

        :param root: The root node of the tree, defaults to None.
        """
        self.root = root
        self.module_path = module_path

    @staticmethod
    def _recursive_build_tree(root: Node) -> Node:
        """
        Recursively build a tree with linked nodes from AST nodes.
        """
        if not isinstance(root, Node):
            raise TypeError("Expected type ast.Module for module_root")

        # Look through fields and their values of the ast node
        for field, value_list in ast.iter_fields(root.node):
            if not value_list:
                continue

            if not isinstance(value_list, list):
                value_list = [value_list]

            for value in value_list:
                if not isinstance(value, ast.AST):
                    continue

                tree_node = Node(value, parent=root, children=[], parent_child_re=field)
                root.children.append(tree_node)
                ModuleTree._recursive_build_tree(tree_node)

        return root

    def build_tree(self, module_ast_node: ast.Module) -> Node:
        """
        Build a tree structure from a root node by exploring the AST tree.

        :param module_ast_node: The top AST node of a module.
        :return: TreeNode object at the root of the built tree.
        """
        module_node = ModuleNode(module_ast_node, None, [], self.module_path)
        return self._recursive_build_tree(module_node)

    @staticmethod
    def get_ast_module_node(module_path: Path) -> ast.Module:
        """
        Parse a Python module file and return its AST representation.

        :param module_path: The path to the Python module file.
        :return: The AST representation of the module.
        """
        with open(module_path, "r", encoding="utf-8") as file:
            module_ast_node = ast.parse(file.read())
            return module_ast_node

    def print_tree(self, indent: str = "", is_last: bool = True) -> None:
        """
        Print the tree structure starting from the given node.

        :param node: The TreeNode to start printing from.
        :param indent: The indentation string for the current level.
        :param is_last: Whether the current node is the last child.
        """
        self._recursive_print_tree(self.root, indent, is_last)

    @staticmethod
    def _recursive_print_tree(
        node: Node, indent: str = "", is_last: bool = True
    ) -> None:
        """
        Recursively print the tree structure.
        """
        # print(node)
        connector = "└── " if is_last else "├── "
        print(indent + connector + f"<{node.parent_child_re}> ── " + repr(node))

        # Prepare next level's indent
        if is_last:
            new_indent = indent + "    "
        else:
            new_indent = indent + "│   "

        # Recurse on children
        if node.children:
            for i, child in enumerate(node.children):
                is_last_child = i == len(node.children) - 1
                ModuleTree._recursive_print_tree(child, new_indent, is_last_child)

    @classmethod
    def create_module_tree(cls, module_path: Path) -> "ModuleTree":
        """
        Create module tree from a module path.

        :return: ModuleTree object
        """
        module_ast_node = cls.get_ast_module_node(module_path)
        root = cls.build_tree(module_ast_node, module_path)
        root.module_path = module_path

        return cls(root=root)

    def search_tree_by_str(self, search_keys: str) -> List[Node]:
        """
        Search the tree for nodes containing the given string in their representation.

        :param search_keys: The string to search for in the tree nodes.
        :param result: A list to store the search results.
        :return: A list of TreeNodes matching the search criteria.
        """
        result = []
        return self._recursive_search_tree_by_str(self.root, search_keys, result)

    @staticmethod
    def _recursive_search_tree_by_str(
        root: Node, search_keys: str, result: List
    ) -> List[Node]:
        """
        Recursively search the tree for nodes containing the given string.
        """
        if search_keys in root.__repr__():
            result.append(root)

        for node in root.children:
            result += ModuleTree._recursive_search_tree_by_str(node, search_keys, [])

        return result

    @staticmethod
    def _recursive_search_func_ref(root, func_name, result=None) -> List:
        """Recursively search function refenrence by function name."""
        if result is None:
            result = []

        if isinstance(root.node, ast.Call):
            func_node = root.node.func
            if isinstance(func_node, ast.Name) and func_node.id == func_name:
                result.append(root)
            elif isinstance(func_node, ast.Attribute) and func_node.attr == func_name:
                result.append(root)

        for child in root.children:
            result += ModuleTree._recursive_search_func_ref(child, func_name, [])

        return result

    @staticmethod
    def _recursive_search_class_ref(root, class_name, result=None):
        """Recursively search for class reference by class name."""
        if isinstance(root.node, ast.Name) and root.node.id == class_name:
            result.append(root)
        elif isinstance(root.node, ast.Attribute) and root.node.attr == class_name:
            result.append(root)

        for child in root.children:
            result += ModuleTree._recursive_search_class_ref(child, class_name, [])

        return result

    def search_function_reference(self, func_name) -> List["Node"]:
        result = []
        return self._recursive_search_func_ref(self.root, func_name, result)

    def search_class_reference(self, class_name) -> List[Node]:
        result = []
        return self._recursive_search_class_ref(self.root, class_name, result)

    @staticmethod
    def _recursive_search_class_definition(root, result=None):
        if isinstance(root.node, ast.ClassDef):
            result.append(root)

        for child in root.children:
            result += ModuleTree._recursive_search_class_definition(child, [])

        return result

    def search_class_definition(self):
        result = []
        return self._recursive_search_class_definition(self.root, result)

    @staticmethod
    def _recursive_search_func_definition(root, result=None):
        if isinstance(root.node, ast.FunctionDef):
            result.append(root)

        for child in root.children:
            result += ModuleTree._recursive_search_func_definition(child, [])

        return result

    def search_func_definition(self):
        result = []
        return self._recursive_search_func_definition(self.root, result)

    @staticmethod
    def _recursive_search_func_ref(root, func_name: str, result=None):
        if result is None:
            result = []

        if isinstance(root.node, ast.Call):
            func_node = root.node.func
            if isinstance(func_node, ast.Name) and func_node.id == func_name:
                result.append(root)
            elif isinstance(func_node, ast.Attribute) and func_node.attr == func_name:
                result.append(root)

        for child in root.children:
            result += ModuleTree._recursive_search_func_ref(child, func_name, [])

        return result

    def search_function_reference(self, func_name: str) -> List["Node"]:
        return self._recursive_search_func_ref(self.root, func_name, [])


class ReposTree:
    """Responsible for managing all module trees in a repos and upper modules level-related methods."""

    def __init__(self, repo_path: Union[str, Path]) -> None:
        self.repo_path = repo_path if isinstance(repo_path, Path) else Path(repo_path)

    def get_file_extension(self, filename: str) -> str | None:
        match = re.search(r'\.([^.\\/:*?"<>|\r\n]+)$', filename)
        if match:
            extension = match.group(1)
            return extension
        else:
            return None

    def get_modules(self, repos_path: Path) -> List[Path]:
        """Get all modules in a folder."""
        result = []
        for dirpath, _, filenames in os.walk(repos_path):
            python_files = (
                file for file in filenames if self.get_file_extension(file) == "py"
            )
            # Absolute python file path
            abs_py_files = [Path(dirpath) / Path(file) for file in python_files]
            result += abs_py_files

        return result

    def get_module_trees(self) -> List[ModuleTree]:
        """Get all module trees in the repos."""
        abs_py_files = self.get_modules(self.repo_path)
        self.module_trees = {
            py_file: ModuleTree.create_module_tree(py_file) for py_file in abs_py_files
        }

        return self.module_trees

    def search_tree_by_class(self, class_name: str) -> List[Node]:
        """Search all modules in a tree to find class references."""
        result = []
        for tree in self.module_trees.values():
            result += tree.search_class_reference(class_name)

        return result

    def search_tree_by_function(self, func_name: str) -> List[Node]:
        """Search all modules in a tree to find class references."""
        result = []
        for tree in self.module_trees.values():
            result += tree.search_function_reference(func_name)

        return result

    def get_class_definition(self):
        result = []
        for tree in self.module_trees.values():
            result += tree.search_class_definition()

        return result

    def get_func_definition(self):
        result = []
        for tree in self.module_trees.values():
            result += tree.search_func_definition()

        return result
