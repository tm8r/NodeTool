# -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from . import node
from . import port
from . import line
import xml.etree.ElementTree as ET
import glob
import os
import json


class PortColor(object):
    Int = QtCore.Qt.red
    Bool = QtCore.Qt.green

    def __setattr__(self, *_):
        pass


def get_node_file_list():
    path = get_xml_dir()
    for f in glob.glob(r'{}\*.xml'.format(path)):
        yield f


def get_xml_dir():
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.normpath(os.path.join(base, 'node_db'))
    return path


def create_node_for_xml(xml_file='', view=None):
    _dir = get_xml_dir()
    tree = ET.parse('{}\{}.xml'.format(_dir, xml_file))
    n = node.Node(name=xml_file, label=tree._root.attrib['Label'])
    p = tree.findall('Port')
    create_ports_for_xml(p, n, view)
    n.deploying_port()
    return n


def create_node_for_save_data(view, save_data):
    node = create_node_for_xml(save_data['name'], view)
    view.add_item(node)
    load_node_data(node, save_data, False)


def create_history(*args):
    print 'create_history'


def create_ports_for_xml(ports_xml, parent, view):
    port_color = PortColor()
    for _p in ports_xml:
        if isinstance(parent, node.Node):
            pp = parent.add_port(label=_p.attrib.get('Label'), port_type=_p.attrib.get('Type'),
                                 color=getattr(port_color, _p.attrib.get('ValueType')),
                                 value_type=_p.attrib.get('ValueType'))
        else:
            pp = port.Port(parent=parent, label=_p.attrib.get('Label'), port_type=_p.attrib.get('Type'),
                           color=getattr(port_color, _p.attrib.get('ValueType')), value_type=_p.attrib.get('ValueType'))
        # pp.expanded.connect(create_history)
        _p_find = _p.findall('Port')
        create_ports_for_xml(_p_find, pp, view)


def load_node_data(node, save_data, ports_only=False):
    for _p in node.children_ports_all_iter():
        _p.children_port_expand = save_data['ports'][_p.name]
    node.deploying_port()
    if ports_only:
        return
    node.id = save_data['id']
    node.setZValue(save_data['z_value'])
    node.setX(save_data['x'])
    node.setY(save_data['y'])


def scene_save(view):
    nodes = [_n for _n in node.Node.scene_nodes_iter(view)]
    lines = [_l for _l in line.Line.scene_lines_iter(view)]
    save_data = get_save_data(nodes, lines)
    not_escape_json_dump(r'c:\temp\node_tool.json', save_data)


def get_save_data(nodes, lines):
    save_data = {}
    save_data['node'] = [_n.save_data for _n in nodes]
    save_data['line'] = [_l.save_data for _l in lines]
    return save_data


def load_save_data(data, view):
    nodes = []
    for _n in data['node']:
        node = create_node_for_xml(_n['name'], view)
        view.add_item_on_center(node)
        load_node_data(node, _n, False)
        nodes.append(node)

    for _l in data['line']:
        line_connect_for_save_data(_l, view)

    for _n in nodes:
        for _p in _n.children_ports_all_iter():
            _p.create_temp_line()

    return nodes


def scene_load(view):
    data = not_escape_json_load(r'c:\temp\node_tool.json')
    view.clear()
    load_save_data(data, view)


def line_connect_for_save_data(line_data, view):
    new_line = line.Line(QtCore.QPointF(0, 0), QtCore.QPointF(0, 0), None)
    for _n in node.Node.scene_nodes_iter(view):
        if line_data['source']['node_id'] == _n.id:
            source = _n.port[line_data['source']['port_name']]
        if line_data['target']['node_id'] == _n.id:
            target = _n.port[line_data['target']['port_name']]
    source.connect_line(new_line)
    target.connect_line(new_line)
    new_line.color = target.color
    view.add_item(new_line)


def not_escape_json_dump(path, data):
    # http://qiita.com/tadokoro/items/131268c9a0fd1cf85bf4
    # 日本語をエスケープさせずにjsonを読み書きする
    text = json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2)
    with open(path, 'w') as fh:
        fh.write(text.encode('utf-8'))


def not_escape_json_load(path):
    if os.path.isfile(path) is False:
        return None
    with open(path) as fh:
        data = json.loads(fh.read(), "utf-8")
    return data


def get_lines_related_with_node(nodes, view):
    # 指定ノードに関連するラインをシーン内から取得
    nodes_id = [_n.id for _n in nodes]
    related_lines = []
    for _l in line.Line.scene_lines_iter(view):
        if _l.source.node.id in nodes_id and  _l.target.node.id in nodes_id:
            related_lines.append(_l)
    return related_lines


def refresh_all_node_id_in_scene(view):
    for _n in node.Node.scene_nodes_iter(view):
        _n.refresh_id()

# -----------------------------------------------------------------------------
# EOF
# -----------------------------------------------------------------------------
