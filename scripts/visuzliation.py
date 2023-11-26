from graphviz import Digraph

from vrdu.utils import load_json


def draw_dot(annotations, format="svg", rankdir="TB"):
    """
    format: png | svg | ...
    rankdir: TB (top to bottom graph) | LR (left to right)
    """
    assert rankdir in ["LR", "TB"]

    nodes = set()
    edges = []
    for annotation in annotations:
        nodes.add(annotation["from"])
        nodes.add(annotation["to"])
        edges.append((annotation["from"], annotation["type"], annotation["to"]))

    dot = Digraph(format=format, graph_attr={"rankdir": rankdir})

    for node in nodes:
        dot.node(
            name=str(id(node)),
            label=str(node),
            shape="record",
        )

    for node1, relation, node2 in edges:
        dot.edge(str(id(node1)), str(id(node2)), label=relation)

    return dot


if __name__ == "__main__":
    annotation_file = (
        "/home/PJLAB/maosong/vrdu_data/icml2022/output/result/order_annotation.json"
    )
    annotations = load_json(annotation_file)
    dot = draw_dot(annotations)
    dot.render(filename="gout.dot", view=True)
