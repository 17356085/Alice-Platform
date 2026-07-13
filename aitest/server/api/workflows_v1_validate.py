"""Workflow validation logic (P8-3)"""

def validate_workflow_graph(graph, node_ids):
    """静态校验工作流图
    
    Returns: (errors: list[str], warnings: list[str])
    """
    errors = []
    warnings = []

    # 1. 检查节点 ID 唯一性
    if len(node_ids) != len(set(node_ids)):
        errors.append("Duplicate node IDs found")

    # 2. 检查边引用的节点存在
    node_id_set = set(node_ids)
    for edge in graph.edges:
        if not edge.condition:
            errors.append(f"Edge {edge.from_node}->{edge.to_node} has an empty condition")
        if edge.from_node not in node_id_set:
            errors.append(f"Edge references non-existent node: {edge.from_node}")
        if edge.to_node not in node_id_set:
            errors.append(f"Edge references non-existent node: {edge.to_node}")

    # 3. 检查 agent 节点的 agent_id 非空
    for node in graph.nodes:
        if node.type == "agent" and not node.agent_id:
            errors.append(f"Agent node {node.node_id} missing agent_id")
        if node.type == "condition" and not node.condition_expr:
            errors.append(f"Condition node {node.node_id} missing condition_expr")
        if node.type == "parallel":
            children = node.metadata.get("parallel_nodes", [])
            if not children:
                errors.append(f"Parallel node {node.node_id} has no parallel_nodes")
            elif any(child not in node_id_set for child in children):
                errors.append(f"Parallel node {node.node_id} references an unknown sub-node")
            if int(node.metadata.get("max_concurrency", 1) or 0) < 1:
                errors.append(f"Parallel node {node.node_id} max_concurrency must be positive")

    # 4. 检查孤立节点（无入边且无出边）
    nodes_with_edges = set()
    for edge in graph.edges:
        nodes_with_edges.add(edge.from_node)
        nodes_with_edges.add(edge.to_node)

    for node_id in node_ids:
        if node_id not in nodes_with_edges:
            warnings.append(f"Node {node_id} is isolated (no edges)")

    # 5. 循环检测（DFS）
    def has_cycle() -> bool:
        """检测有向图是否有环"""
        # 构建邻接表
        adj = {nid: [] for nid in node_ids}
        for edge in graph.edges:
            if edge.from_node in adj and edge.to_node in adj:
                adj[edge.from_node].append(edge.to_node)

        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for nid in node_ids:
            if nid not in visited:
                if dfs(nid):
                    return True
        return False

    if has_cycle():
        errors.append("Workflow contains cycles")

    # 6. 可达性检查（找出入度为 0 的起点）
    in_degree = {nid: 0 for nid in node_ids}
    for edge in graph.edges:
        if edge.to_node in in_degree:
            in_degree[edge.to_node] += 1

    entry_nodes = [nid for nid, deg in in_degree.items() if deg == 0]
    if not entry_nodes and node_ids:
        warnings.append("No entry nodes found (all nodes have incoming edges)")

    # 从入口节点 BFS 可达性
    if entry_nodes:
        reachable = set()
        queue = entry_nodes[:]
        adj = {nid: [] for nid in node_ids}
        for edge in graph.edges:
            if edge.from_node in adj and edge.to_node in adj:
                adj[edge.from_node].append(edge.to_node)

        while queue:
            node = queue.pop(0)
            if node in reachable:
                continue
            reachable.add(node)
            for neighbor in adj.get(node, []):
                if neighbor not in reachable:
                    queue.append(neighbor)

        unreachable = set(node_ids) - reachable
        if unreachable:
            warnings.append(f"Unreachable nodes: {', '.join(sorted(unreachable))}")

    return errors, warnings
