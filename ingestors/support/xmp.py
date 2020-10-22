"""
Parses XMP metadata from PDF files.
By Matt Swain. Released under the MIT license.
https://matt-swain.com/blog/2012-06-22-python-xmp-parser-for-pdf-metadata
"""
from collections import defaultdict
from xml.etree import ElementTree as ET

RDF_NS = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
XML_NS = "{http://www.w3.org/XML/1998/namespace}"
NS_MAP = {
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
    "http://purl.org/dc/elements/1.1/": "dc",
    "http://ns.adobe.com/xap/1.0/": "xap",
    "http://ns.adobe.com/pdf/1.3/": "pdf",
    "http://ns.adobe.com/xap/1.0/mm/": "xapmm",
    "http://ns.adobe.com/pdfx/1.3/": "pdfx",
    "http://prismstandard.org/namespaces/basic/2.0/": "prism",
    "http://crossref.org/crossmark/1.0/": "crossmark",
    "http://ns.adobe.com/xap/1.0/rights/": "rights",
    "http://www.w3.org/XML/1998/namespace": "xml",
}


class XMPParser(object):
    def __init__(self, xmp):
        self.tree = ET.XML(xmp)
        self.rdftree = self.tree.find(RDF_NS + "RDF")

    @property
    def meta(self):
        """A dictionary of all the parsed metadata."""
        meta = defaultdict(dict)
        for desc in self.rdftree.findall(RDF_NS + "Description"):
            for el in desc.getchildren():
                ns, tag = self._parse_tag(el)
                meta[ns][tag] = self._parse_value(el)
        return dict(meta)

    def _parse_tag(self, el):
        """Extract the namespace and tag from an element."""
        ns = None
        tag = el.tag
        if tag[0] == "{":
            ns, tag = tag[1:].split("}", 1)
            ns = NS_MAP.get(ns, ns)
        return ns, tag

    def _parse_value(self, el):
        """Extract the metadata value from an element."""
        if el.find(RDF_NS + "Bag") is not None:
            value = []
            for li in el.findall(RDF_NS + "Bag/" + RDF_NS + "li"):
                value.append(li.text)
        elif el.find(RDF_NS + "Seq") is not None:
            value = []
            for li in el.findall(RDF_NS + "Seq/" + RDF_NS + "li"):
                value.append(li.text)
        elif el.find(RDF_NS + "Alt") is not None:
            value = {}
            for li in el.findall(RDF_NS + "Alt/" + RDF_NS + "li"):
                value[li.get(XML_NS + "lang")] = li.text
        else:
            value = el.text
        return value
