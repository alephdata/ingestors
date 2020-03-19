import logging

from followthemoney import model
from followthemoney.graph import Graph
from followthemoney.types import registry

from aleph.index import entities as index
from aleph.logic.entities import entity_expand_nodes


log = logging.getLogger(__name__)


class AlephGraph(Graph):
    def queue(self, id_, proxy=None):
        if id_ not in self.proxies:
            if proxy is None:
                entity = index.get_entity(id_)
                proxy = model.get_proxy(entity)
            if proxy is not None:
                self.proxies[id_] = proxy

    def resolve(self):
        for id_, proxy in self.proxies.items():
            node_id = registry.entity.node_id_safe(id_)
            node = self.nodes.get(node_id)
            if node is not None:
                node.proxy = proxy
                if node.schema is None:
                    node.schema = proxy.schema

    def to_dict(self):
        return {
            'nodes': self.nodes.values(),
            'edges': self.edges.values()
        }


def expand_entity_graph(entity, properties=None, authz=None):
    edge_types = [registry.name.name, registry.email.name,
                  registry.identifier.name, registry.iban.name,
                  registry.phone.name, registry.address.name,
                  registry.url.name, registry.checksum.name,
                  registry.entity.name]
    graph = AlephGraph(edge_types=edge_types)
    graph.add(model.get_proxy(entity))
    for prop, total, entities in entity_expand_nodes(
        entity, properties=properties, include_entities=True, authz=authz
    ):
        for ent in entities:
            proxy = model.get_proxy(ent)
            graph.add(proxy)
    graph.resolve()
    return graph
