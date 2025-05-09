from oo_scanner.tree import ReposTree
from graphviz import Digraph

from pathlib import Path
import ast


class VisManager:
    """
    Responsible for plotting visualization and trigger run and search tree
    based on user preference.
    """

    def __init__(self, repos_path: str, func_included: bool = True):
        self.repos_path = repos_path
        self.func_included = func_included

    def _build_search_tree(self) -> None:
        self.repo_tree = ReposTree(self.repos_path)
        self.tree_dict = self.repo_tree.get_module_trees()  # Side effect: build tree

    @staticmethod
    def visualize_refs_as_graph(
        class_refs, func_refs, func_defs, label="Reference Graph"
    ):
        dot = Digraph(comment=label)
        dot.attr(rankdir="LR", size="12,12")

        def sanitize_id(path: Path, name: str, suffix: str = "") -> str:
            base = str(path).replace("/", "_").replace(".", "_")
            return f"{base}_{name}_{suffix}".strip("_")

        def add_definition_node(name, kind):
            shape = "box" if kind == "class" else "ellipse"
            fill = "lightblue" if kind == "class" else "lightgreen"
            node_id = f"{kind}_{name}"
            dot.node(
                node_id,
                f"{kind.upper()}: {name}",
                shape=shape,
                style="filled",
                fillcolor=fill,
            )

        def add_reference_node(ref_name, ref_dict, kind, index):
            module = ref_dict["module"]
            ref_node = ref_dict["ref_node"]
            location = (
                f"{ref_dict.get('class') or ''}.{ref_dict.get('method') or ''}".strip(
                    "."
                )
            )

            try:
                line_info = f"L{ref_node.lineno}"
            except AttributeError:
                line_info = ""

            label = f"{location}\\n{module.name}\\n{line_info}"
            ref_id = sanitize_id(module, ref_name, f"{kind}_{index}")
            shape = "note"
            fill = "#f0f0f0"
            dot.node(ref_id, label, shape=shape, style="filled", fillcolor=fill)

            # Connect definition to reference, with type_of_ref on edge
            def_id = f"{kind}_{ref_name}"
            edge_label = ref_dict.get("type_of_ref", "Unknown")
            dot.edge(def_id, ref_id, label=edge_label)

        # Add referenced class definitions
        for class_name, refs in class_refs.items():
            if refs:  # only if referenced
                add_definition_node(class_name, "class")
                for idx, ref in enumerate(refs):
                    add_reference_node(class_name, ref, "class", idx)

        # Add referenced function definitions
        for func_name, refs in func_refs.items():
            if refs:
                add_definition_node(func_name, "func")
                for idx, ref in enumerate(refs):
                    add_reference_node(func_name, ref, "func", idx)

                # Link method to class if known
                for func_def in func_defs:  # Loop through function definitions
                    if func_def.node.name == func_name:
                        class_name = func_def.get("class")
                        if class_name and class_name in class_refs:
                            dot.edge(
                                f"class_{class_name}",
                                f"func_{func_name}",
                                style="dashed",
                                label="method-of",
                            )
                        break  # Stop after finding the first match for the function

        return dot

    def visualize(self):
        class_defs = self.repo_tree.get_class_definition()
        func_defs = self.repo_tree.get_func_definition()

        class_refs = self.get_class_ref(class_defs)
        func_refs = self.get_func_ref(func_defs)

        dot = self.visualize_refs_as_graph(class_refs, func_refs, func_defs)
        dot.render("ref_graph", view=True)

    @staticmethod
    def get_class_ref_type(node):
        parent_node = node.parent
        if isinstance(parent_node, ast.Call) and parent_node.func is node:
            return "Instantiation"
        elif isinstance(parent_node, ast.ClassDef) and node in parent_node.bases:
            return "Inheritance"
        elif isinstance(parent_node, ast.AnnAssign) and parent_node.annotation is node:
            return "Variable Type Hint"
        elif isinstance(parent_node, ast.arg) and parent_node.annotation is node:
            return "Function Arg Type Hint"
        elif isinstance(parent_node, ast.FunctionDef) and parent_node.returns is node:
            return "Function Return Type Hint"
        elif isinstance(parent_node, ast.Assign):
            return "Assigned Class (maybe used as a value)"
        elif isinstance(parent_node, ast.Attribute):
            return "Attribute Access"
        return "Unknown"

    @staticmethod
    def get_func_ref_type(node):
        parent_node = node.parent
        if isinstance(parent_node, ast.Call) and parent_node.func is node:
            return "Function Call"
        elif isinstance(parent_node, ast.FunctionDef) and parent_node.name == node.id:
            return "Function Definition"
        elif isinstance(parent_node, ast.ClassDef) and node in parent_node.bases:
            return "Function in Inheritance"
        elif isinstance(parent_node, ast.arg) and parent_node.annotation is node:
            return "Function Arg Type Hint"
        elif isinstance(parent_node, ast.FunctionDef) and parent_node.returns is node:
            return "Function Return Type Hint"
        elif isinstance(parent_node, ast.Attribute):
            return "Function Attribute Access"
        return "Unknown"

    # Search for func ref
    def get_func_ref(self, func_defs):
        result = {}

        for class_def in func_defs:
            temp_re = self.repo_tree.search_tree_by_function(class_def.node.name)
            result[class_def.node.name] = []
            for ref in temp_re:
                temp_dict = {}
                temp_dict["ref_node"] = ref
                temp_dict["method"] = ref.get_enclosing_function()
                temp_dict["class"] = ref.get_enclosing_class()
                temp_dict["module"] = ref.get_enclosing_module()
                temp_dict["type_of_ref"] = self.get_func_ref_type(ref)

                result[class_def.node.name].append(temp_dict)

        return result

    # Search for class ref
    def get_class_ref(self, class_defs):
        result = {}

        for class_def in class_defs:
            temp_re = self.repo_tree.search_tree_by_class(class_def.node.name)
            result[class_def.node.name] = []
            for ref in temp_re:
                temp_dict = {}
                temp_dict["ref_node"] = ref
                temp_dict["method"] = ref.get_enclosing_function()
                temp_dict["class"] = ref.get_enclosing_class()
                temp_dict["module"] = ref.get_enclosing_module()
                temp_dict["type_of_ref"] = self.get_class_ref_type(ref)

                result[class_def.node.name].append(temp_dict)

        return result
