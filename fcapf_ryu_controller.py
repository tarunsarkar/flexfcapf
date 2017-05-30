# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import json
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from webob import Response
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib import dpid as dpid_lib
from ryu.topology.api import get_switch, get_link, get_host
import logging

LOG = logging.getLogger('ryu.controller.controller')

fcapf_controller_instance = 'fcapf_network_controller'

class FCAPFNetworkController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(FCAPFNetworkController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.switches = {}
        wsgi = kwargs['wsgi']
        wsgi.register(ControllerRequestProcessor, {fcapf_controller_instance: self})

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.switches[datapath.id] = datapath
        self.mac_to_port.setdefault(datapath.id, {})


class ControllerRequestProcessor(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(ControllerRequestProcessor, self).__init__(req, link, data, **config)
        self.fcapf_network_controller = data[fcapf_controller_instance]

    @route('fcapfnetworkcontroller', '/fcapfnetworkcontroller/flowtable/addflows', methods=['PUT'])
    def add_flows(self, req, **kwargs):
        try:
            entries = req.json if req.body else {}
            for entry in entries:
                dpid = entry['dpid']
                payload = entry['payload']
                self._set_flow_table(dpid, payload)
            status = 200
        except ValueError:
            LOG.error("Wrong input!!")
            status = 400
        except:
            status = 400
        return Response(status=status)

    @route('fcapfnetworkcontroller', '/fcapfnetworkcontroller/flowtable/addflow/{dpid}', methods=['PUT'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def add_flow(self, req, **kwargs):
        try:
            entry = req.json if req.body else {}
            self._set_flow_table(kwargs['dpid'], entry)
            status = 200
        except ValueError:
            LOG.error("Wrong input!!")
            status = 400
        except:
            status = 400
        return Response(status=status)

    @route('fcapfnetworkcontroller', '/fcapfnetworkcontroller/flowtable/delflows', methods=['PUT'])
    def del_flows(self, req, **kwargs):
        try:
            entries = req.json if req.body else {}
            for entry in entries:
                dpid = entry['dpid']
                payload = entry['payload']
                self._delete_flow_table(dpid, payload)
            status = 200
        except ValueError:
            LOG.error("Wrong input!!")
            status = 400
        except:
            status = 400
        return Response(status=status)

    @route('fcapfnetworkcontroller', '/fcapfnetworkcontroller/flowtable/delflow/{dpid}', methods=['PUT'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def del_flow(self, req, **kwargs):
        try:
            entry = req.json if req.body else {}
            self._delete_flow_table(kwargs['dpid'], entry)
            status = 200
        except ValueError:
            LOG.error("Wrong input!!")
            status = 400
        except:
            status = 400
        return Response(status=status)

    def _set_flow_table(self, dpid_str, entry):
        try:
            dpid = dpid_lib.str_to_dpid(dpid_str)
            contr_inst = self.fcapf_network_controller
            if dpid not in contr_inst.mac_to_port:
                return Response(status=404)
            datapath = contr_inst.switches.get(dpid)
            dl_type=entry['dltype']
            action = entry['action']
            if action == 'normal':
                action = ofproto_v1_3.OFPP_NORMAL

            ip_src = entry['ipsrc']
            ip_dest = entry['ipdest']
            if datapath is not None:
                parser = datapath.ofproto_parser
                # from known device to new device
                actions = [parser.OFPActionOutput(action)]
                if dl_type == "ip":
                    port = entry['inport']
                    match = parser.OFPMatch(in_port=port, ipv4_src=ip_src,
                        ipv4_dst=ip_dest, eth_type=0x0800)
                elif dl_type == "arp":
                    match = parser.OFPMatch(arp_spa=ip_src,
                        arp_tpa=ip_dest, eth_type=0x0806)
                else:
                    LOG.error("Wrong input!!")
                self._add_flow(datapath, 1, match, actions)
            else:
                LOG.error("Datapath not found!!")
        except:
            LOG.error("Unexpected error in _set_flow_table:", sys.exc_info()[0])
            raise

    def _delete_flow_table(self, dpid_str, entry):
        try:
            dpid = dpid_lib.str_to_dpid(dpid_str)
            contr_inst = self.fcapf_network_controller
            if dpid not in contr_inst.mac_to_port:
                return Response(status=404)
            datapath = contr_inst.switches.get(dpid)
            dl_type=entry['dltype']
            ip_src = entry['ipsrc']
            ip_dest = entry['ipdest']
            if datapath is not None:
                parser = datapath.ofproto_parser
                # from known device to new device
                if dl_type == "ip":
                    port = entry['inport']
                    match = parser.OFPMatch(in_port=port, ipv4_src=ip_src,
                        ipv4_dst=ip_dest, eth_type=0x0800)
                elif dl_type == "arp":
                    match = parser.OFPMatch(arp_spa=ip_src,
                        arp_tpa=ip_dest, eth_type=0x0806)
                else:
                    LOG.error("Wrong input!!")
                self._del_flow(datapath, match)
            else:
                LOG.error("Datapath not found!!")
        except:
            LOG.error("Unexpected error in _delete_flow_table:", sys.exc_info()[0])
            raise

    def _add_flow(self, datapath, priority, match, actions, buffer_id=None):
        try:
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser

            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                 actions)]
            if buffer_id:
                # mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                #                         priority=priority, match=match,
                #                         instructions=inst, idle_timeout=300)
                mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                        priority=priority, match=match,
                                        instructions=inst)
            else:
                # mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                #                         match=match, instructions=inst, idle_timeout=300)
                mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                        match=match, instructions=inst)
            datapath.send_msg(mod)
        except:
            LOG.error("Unexpected error in _add_flow:", sys.exc_info()[0])
            raise

    def _del_flow(self, datapath, match):
        try:
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            mod = parser.OFPFlowMod( datapath, command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                priority=1, match=match)
            datapath.send_msg(mod)
        except:
            LOG.error("Unexpected error in _del_flow:", sys.exc_info()[0])
            raise

    @route('fcapfnetworkcontroller', '/fcapfnetworkcontroller/topology/switches', methods=['GET'])
    def list_switches(self, req, **kwargs):
        return self._switches(req, **kwargs)

    @route('fcapfnetworkcontroller', '/fcapfnetworkcontroller/topology/switches/{dpid}', methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def get_switch(self, req, **kwargs):
        return self._switches(req, **kwargs)

    @route('fcapfnetworkcontroller', '/fcapfnetworkcontroller/topology/links', methods=['GET'])
    def list_links(self, req, **kwargs):
        return self._links(req, **kwargs)

    @route('fcapfnetworkcontroller', '/fcapfnetworkcontroller/topology/links/{dpid}', methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def get_links(self, req, **kwargs):
        return self._links(req, **kwargs)

    @route('fcapfnetworkcontroller', '/fcapfnetworkcontroller/topology/hosts', methods=['GET'])
    def list_hosts(self, req, **kwargs):
        return self._hosts(req, **kwargs)

    @route('fcapfnetworkcontroller', '/fcapfnetworkcontroller/topology/hosts/{dpid}', methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def get_hosts(self, req, **kwargs):
        return self._hosts(req, **kwargs)

    def _switches(self, req, **kwargs):
        try:
            dpid = None
            if 'dpid' in kwargs:
                dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
            switches = get_switch(self.fcapf_network_controller, dpid)
            body = json.dumps([switch.to_dict() for switch in switches])
        except:
            LOG.error("Unexpected error in _links:", sys.exc_info()[0])
        return Response(content_type='application/json', body=body)

    def _links(self, req, **kwargs):
        try:
            dpid = None
            if 'dpid' in kwargs:
                dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
            links = get_link(self.fcapf_network_controller, dpid)
            # customlinks = [link.to_dict() for link in links]
            # body = json.dumps([self._preciselink(link) for link in customlinks])
            body = json.dumps([link.to_dict() for link in links])
        except:
            LOG.error("Unexpected error in _links:", sys.exc_info()[0])
        return Response(content_type='application/json', body=body)

    def _hosts(self, req, **kwargs):
        try:
            dpid = None
            if 'dpid' in kwargs:
                dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
            hosts = get_host(self.fcapf_network_controller, dpid)
            body = json.dumps([host.to_dict() for host in hosts])
        except:
            LOG.error("Unexpected error in _links:", sys.exc_info()[0])
        return Response(content_type='application/json', body=body)

    def _preciselink(self, link):
        try:
            plink={
                'src':{
                    'port_no': link['src']['port_no'],
                    'dpid': link['src']['dpid']
                },
                'dst':{
                    'port_no': link['dst']['port_no'],
                    'dpid': link['dst']['dpid']
                }
            }
        except:
            LOG.error("Unexpected error in _links:", sys.exc_info()[0])
        return plink
