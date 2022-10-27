import graphviz
from typing import List
from thoth.app.decompiler.variable import Operand, OperandType, Variable
from thoth.app.disassembler.function import Function


class Tainting:
    FULL_TAINTED_COLOR = (1.0, 0.0, 0.0)
    PROPAGATION_COEFFICIENT = 0.7

    @classmethod
    def _get_taint(cls, coefficient: float) -> str:
        """
        Get the hexadecimal color from a tainting coefficient
        1.  -> #ff00000 (red)
        0.5 -> #ff7f7f (light red)
        0.  -> #ffffff (white)
        """
        hsv_tuple_taint = tuple(
            map(sum, zip(cls.FULL_TAINTED_COLOR, (0, coefficient, coefficient)))
        )
        rgb_values = (
            int(hsv_tuple_taint[0] * 255),
            int((1 - hsv_tuple_taint[1]) * 255),
            int((1 - hsv_tuple_taint[2]) * 255),
        )
        hex_taint = "#%02x%02x%02x" % (rgb_values[0], rgb_values[1], rgb_values[2])
        return hex_taint


class DFGVariableBlock:
    """
    DFG Variable block class
    """

    def __init__(self, name: str, function: Function, is_function_argument: bool) -> None:
        self.name = name
        self.graph_representation_name = None
        self.function = function
        self.is_function_argument = is_function_argument
        self.tainting_coefficient = 0
        self.parents_blocks: List[DFGVariableBlock] = []
        self.children_blocks: List[DFGVariableBlock] = []


class DFGEdge:
    """
    DFG Edge class
    """

    def __init__(
        self, source: DFGVariableBlock, destination: DFGVariableBlock, function: Function
    ) -> None:
        self.source = source
        self.destination = destination
        self.function = function


class DFG:
    """
    DataFlow Graph class
    """

    def __init__(self, variables: List[Variable]) -> None:
        self.variables = variables
        self.variables_blocks: List[DFGVariableBlock] = []
        self.edges: List[DFGEdge] = []
        # List of all the functions arguments names
        all_functions: List[Function] = list(filter(None, [v.function for v in self.variables]))
        self.all_functions_arguments = list(sum([f.arguments_list() for f in all_functions], []))
        self.dot = None

    def _clean_tainting(self) -> None:
        """
        Remove all tainting from variables
        """
        for block in self.variables_blocks:
            block.tainting_coefficient = 0

    def get_variable_name(self, variable: DFGVariableBlock) -> str:
        """
        Get the name of a variable that will be displayed in the graph representation
        """
        if variable.name in self.all_functions_arguments:
            return "f%s_%s" % (variable.function.id, variable.name)
        return variable.name

    @staticmethod
    def taint_children_blocks(parent_block: DFGVariableBlock) -> None:
        """
        Taint the children of a block
        """
        for child_block in parent_block.children_blocks:
            child_block.tainting_coefficient = (
                Tainting.PROPAGATION_COEFFICIENT * parent_block.tainting_coefficient
            )

    def _taint_variable(self, source_block: DFGVariableBlock) -> None:
        """
        Taint all the variables than inherit from a parent variable
        """
        tainted_blocks = []

        # Taint root variable
        source_block.tainting_coefficient = 1

        # Taint children variables
        blocks_to_taint = [source_block]
        while blocks_to_taint:
            self.taint_children_blocks(blocks_to_taint[0])
            tainted_blocks.append(blocks_to_taint[0])
            for block in blocks_to_taint[0].children_blocks:
                if not block in tainted_blocks:
                    blocks_to_taint.append(block)
            blocks_to_taint.pop(0)

    def _taint_functions_arguments(self) -> None:
        """
        Taint the functions arguments
        """
        for variable in self.variables_blocks:
            if variable.is_function_argument:
                self._taint_variable(variable)

    def _create_blocks(self) -> None:
        """
        Create the DFG blocks from the variables
        """
        for variable in self.variables:
            variable_name = variable.name
            variable_function = variable.function
            is_function_argument = False

            if variable_function is not None:
                function_arguments = variable.function.arguments_list(implicit=False, ret=False)
                is_function_argument = variable_name in function_arguments
                # Create block
                new_block = DFGVariableBlock(variable_name, variable_function, is_function_argument)
                new_block.graph_representation_name = self.get_variable_name(new_block)
                self.variables_blocks.append(new_block)

    def _create_edges(self) -> None:
        """
        Create the DFG edges from the variables
        """
        for variable in self.variables:
            if variable.value is None:
                continue

            destination_block = [
                b
                for b in self.variables_blocks
                if variable.function == b.function and variable.name == b.name
            ][0]

            # Source variables
            parents_variables = [v for v in variable.value.operation if isinstance(v, Operand)]
            parents_variables = [v for v in parents_variables if v.type == OperandType.VARIABLE]

            source_blocks = []
            for parent_variable in parents_variables:
                if isinstance(parent_variable.value, list):
                    source_blocks = [
                        b
                        for b in self.variables_blocks
                        if variable.function == b.function and b.name in parent_variable.value
                    ]
                else:
                    source_blocks = [
                        b
                        for b in self.variables_blocks
                        if variable.function == b.function and b.name == variable.name
                    ]

            for source_block in source_blocks:
                source_block.children_blocks.append(destination_block)
                destination_block.parents_blocks.append(source_block)
                self.edges.append(DFGEdge(source_block, destination_block, variable.function))

    def _create_dfg(self) -> None:
        """
        Create the DFG (Blocks and Edges)
        """
        self._create_blocks()
        self._create_edges()

    def _create_graph_representation(self) -> str:
        """
        Generate a Dot graph layout
        """
        self.dot = graphviz.Digraph("DataFlow Graph", comment="", strict=True)
        contract_functions = list(set([v.function.name for v in self.variables_blocks]))

        # Create one subgraph per function
        subgraphs = []
        for function in contract_functions:
            subgraph = graphviz.Digraph(name="cluster_%s" % function)
            subgraph.attr(label=function)
            subgraphs.append(subgraph)

        # Nodes
        for variable in self.variables_blocks:
            function_subgraph = [
                s for s in subgraphs if s.name == "cluster_%s" % variable.function.name
            ][0]
            function_subgraph.node(
                self.get_variable_name(variable),
                style="filled",
                fillcolor=Tainting._get_taint(variable.tainting_coefficient),
                label=variable.name,
            )

        # Edges
        for edge in self.edges:
            function_subgraph = [
                s for s in subgraphs if s.name == "cluster_%s" % edge.function.name
            ][0]
            if edge.source == edge.destination:
                continue
            if edge.source.function != edge.destination.function:
                continue

            function_subgraph.edge(
                edge.source.graph_representation_name, edge.destination.graph_representation_name
            )
        # Join subgraphs
        [self.dot.subgraph(_) for _ in subgraphs]

        return self.dot.source

    def _print_dfg(self, folder: str, view=False, format: str = "pdf"):
        """
        Open the graph representation
        """
        self.dot.render(directory=folder, view=view, format=format)
