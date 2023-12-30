"""
Created on 2022-06-20

see  
    https://github.com/tyleradams/json-toolkit
    https://stackoverflow.com/questions/36021526/converting-an-array-dict-to-xml-in-python

@author: tyleradams
@author: wf
"""
from xml.dom.minidom import parseString

from dicttoxml2 import dicttoxml


class Lod2Xml:
    """
    convert a list of dicts to XML
    """

    def __init__(
        self, lod, root: str = "root", node_name: callable = (lambda x: "node")
    ):
        """
        construct me with the given list of dicts

        Args:
            lod(list): the list of dicts to convert to XML
            root(str): the name of the root nod
            item_name(func): the function to use to calculate node names
        """
        self.lod = lod
        self.root = root
        self.item_name = node_name

    def asXml(self, pretty: bool = True):
        """
        convert result to XML

        Args:
            pretty(bool): if True pretty print the result

        """
        xml = dicttoxml(
            self.lod, custom_root=self.root, item_func=self.item_name, attr_type=False
        )
        if pretty:
            dom = parseString(xml)
            prettyXml = dom.toprettyxml()
        else:
            prettyXml = xml
        return prettyXml
