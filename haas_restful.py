
from flask import Flask, jsonify, abort, make_response, request
import haas.control
import haas.er
import haas.config
from flask.ext.httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

app = Flask(__name__)


class G():
    pass
g=G()

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@auth.verify_password
def verify_password(username, password):
    g.username=username
    return True


@app.route('/groups', methods = ['GET'])
@auth.login_required
def get_groups():
    print g.username
    groups = []
    for group in  haas.control.query_db(haas.er.Group):
        print group
        groups.append({
                'group_name':group.group_name,
                'vm_name':group.vm_name,
                'network_id':group.network_id,
                'deployed':group.deployed
                })

    return jsonify({'groups': groups} )


@app.route('/groups/<group_name>', methods = ['GET'])
def get_group(group_name):
    group = haas.control.get_entity_by_cond(haas.er.Group,"group_name=='%s'"%group_name)

    group_dict ={
        'group_name': group.group_name,
        'vm_name': group.vm_name,
        'network_id': group.network_id,
        'deployed': group.deployed,
        }
    return jsonify(group_dict)

@app.route('/groups/<group_name>/nodes', methods = ['GET'])
def get_group_nodes(group_name):
    group = haas.control.get_entity_by_cond(haas.er.Group,"group_name=='%s'"%group_name)
    nodes = []
    print group
    for node in group.nodes:
        print node
        nodes.append(node.node_id)
    nodes_dict={"nodes":nodes}
    return jsonify(nodes_dict)

@app.route('/groups/<group_name>/nodes/add/<node_id>',methods = ['POST'])
def add_node_to_group(group_name,node_id):
    node_id = int(node_id)
    group = haas.control.get_entity_by_cond(haas.er.Group,'group_name == "%s"'%group_name)
    node = haas.control.get_entity_by_cond(haas.er.Node, 'node_id == %d'%node_id)
    if not group or not node or node.available == False:
        abort(404)
    node.group = group
    return get_group_nodes(group_name)

@app.route('/groups/<group_name>/nodes/remove/<node_id>',methods = ['DELETE'])
def remove_node_from_group(group_name,node_id):
    node_id = int(node_id)
    group = haas.control.get_entity_by_cond(haas.er.Group,'group_name == "%s"'%group_name)
    node = haas.control.get_entity_by_cond(haas.er.Node, 'node_id == %d'%node_id)
    if not group or not node:
        abort(404)
    node.group = None
    node.available = True
    return get_group_nodes(group_name)



@app.route('/groups', methods = ['POST'])
def create_group():
    if not request.json or not 'group_name' in request.json:
        abort(400)
    group = {
        'group_name': request.json['group_name'],
        'vm_name': request.json['vm_name'],
        'network_id' : request.json['network_id'],
        'deployed' : False
    }
    print group
    haas.control.create_group(group['group_name'],group['vm_name'],group['network_id'])
    groups.append(group)
    return jsonify({ 'group':group}), 201

@app.route('/groups/<group_name>', methods = ['DELETE'])
def destroy_group(group_name):
    haas.control.destroy_group(group_name)
    return get_groups()


'''
new interface begins
'''

@app.route('/nodes',methods = ['POST'])
def create_node():
    node_id = request.json['node_id']
    haas.control.create_node(node_id)
    return jsonify({'node_id':node_id}),201
    
@app.route('/nics',methods=['POST'])
def create_nic():
    nic = {}
    nic["nic_id"] = request.json['nic_id']
    nic["mac_addr"] = request.json['mac_addr']
    nic["name"] = request.json['name']
    haas.control.create_nic(nic["nic_id"],nic["mac_addr"],nic["name"])
    return jsonify(nic),201

@app.route('/switches',methods=['POST'])
def create_switch():
    switch = {}
    switch["switch_id"] = request.json['switch_id']
    switch['script'] = request.json['script']
    haas.control.create_switch(switch['switch_id'],switch['script'])
    return jsonify(switch),201

@app.route('/ports',methods=['POST'])
def create_port():
    port = {}
    port["port_id"] = request.json['port_id']
    port['switch_id'] = request.json['switch_id']
    port['port_no'] = request.json['port_no']
    haas.control.create_port(port['port_id'],port['switch_id'],port['port_no'])
    return jsonify(port),201

if __name__ == '__main__':
    app.run(debug = True)


