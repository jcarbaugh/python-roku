from contextlib import closing

import xml.etree.ElementTree as ET
from six import BytesIO


def deserialize_apps(doc, roku=None):

    from .core import Application

    applications = []
    root = ET.fromstring(doc)
    for elem in root:
        app = Application(
            id=elem.get('id'), version=elem.get('version'), name=elem.text)
        applications.append(app)
    return applications


def serialize_apps(apps):

    root = ET.Element('apps')

    for app in apps:
        attrs = {'id': app.id, 'version': app.version}
        elem = ET.SubElement(root, 'app', attrs)
        elem.text = app.name

    with closing(BytesIO()) as bffr:
        tree = ET.ElementTree(root)
        tree.write(bffr, xml_declaration=True, encoding="utf-8")
        content = bffr.getvalue()

    return content
