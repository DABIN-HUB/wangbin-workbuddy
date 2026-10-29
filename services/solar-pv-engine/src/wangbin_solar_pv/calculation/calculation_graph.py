"""Period/boundary-specific dependency DAG, not an inferred cyclic symbol graph.

The same frozen output may have explicitly different methods or periods. Node
identity records those distinctions; selection is never made by whichever
formula last overwrote a shared dictionary key.
"""
from __future__ import annotations

from dataclasses import dataclass
import heapq

from ..errors import ContractError
from .method_config import PARAMETERS


@dataclass(frozen=True, slots=True)
class CalculationNode:
    node_id: str
    formula_id: str
    dependencies: tuple[str, ...]
    input_field_ids: tuple[str, ...]
    period: str
    boundary_id: str
    selected_method: str
    method_parameter_ids: tuple[str, ...] = ()


class CalculationGraph:
    def __init__(self, nodes, catalog):
        self.nodes = {}
        for node in nodes:
            if not isinstance(node, CalculationNode) or not all(isinstance(v, str) and v for v in (node.node_id, node.formula_id, node.period, node.boundary_id, node.selected_method)):
                raise ContractError("CALCULATION_NODE_SHAPE")
            if node.node_id in self.nodes:
                raise ContractError("DUPLICATE_CALCULATION_NODE")
            if node.formula_id not in catalog.formulas:
                raise ContractError("UNKNOWN_FORMULA", node.formula_id)
            if set(node.input_field_ids) - set(catalog.fields):
                raise ContractError("GRAPH_UNKNOWN_RAW_FIELD")
            if set(node.method_parameter_ids) - set(PARAMETERS):
                raise ContractError("GRAPH_UNKNOWN_METHOD_PARAMETER")
            if len(set(node.dependencies)) != len(node.dependencies):
                raise ContractError("DUPLICATE_DEPENDENCY")
            self.nodes[node.node_id] = node
        self._children = {nid: [] for nid in self.nodes}
        degree = {}
        for nid, node in self.nodes.items():
            degree[nid] = len(node.dependencies)
            for parent in node.dependencies:
                if parent not in self.nodes:
                    raise ContractError("GRAPH_MISSING_DEPENDENCY")
                self._children[parent].append(nid)
        ready = [nid for nid, count in degree.items() if count == 0]
        heapq.heapify(ready)
        self._order = []
        while ready:
            current = heapq.heappop(ready)
            self._order.append(current)
            for child in self._children[current]:
                degree[child] -= 1
                if degree[child] == 0:
                    heapq.heappush(ready, child)
        if len(self._order) != len(self.nodes):
            raise ContractError("CALCULATION_GRAPH_CYCLE")

    def ordered(self):
        return [self.nodes[nid] for nid in self._order]

    def affected_by(self, input_field_ids=(), *, method_parameter_ids=()):
        fields, methods = set(input_field_ids), set(method_parameter_ids)
        affected = set()
        for nid in self._order:
            node = self.nodes[nid]
            if fields.intersection(node.input_field_ids) or methods.intersection(node.method_parameter_ids) or affected.intersection(node.dependencies):
                affected.add(nid)
        return [nid for nid in self._order if nid in affected]

    def snapshot(self):
        return [{"node_id": n.node_id, "formula_id": n.formula_id, "dependencies": list(n.dependencies),
                 "input_field_ids": list(n.input_field_ids), "method_parameter_ids": list(n.method_parameter_ids),
                 "period": n.period, "boundary_id": n.boundary_id, "selected_method": n.selected_method}
                for n in self.ordered()]
