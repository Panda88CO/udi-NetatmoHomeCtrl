#!/usr/bin/env python3

"""
Polyglot v3 node server
Copyright (C) 2023 Universal Devices

MIT License
"""


import time
import traceback
import re
import sys

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

#from NetatmoOauth import NetatmoCloud
from NetatmoOauthHomeCtrl import NetatmoOauthHomeCtrl
from  udiNetatmoHomeCtrlRoom import udiNetatmoHomeCtrlRoom, udiNetatmoEnergyRoom
#from nodes.controller import Controller
#from udi_interface import logging, Custom, Interface
version = '0.1.8'

#polyglot = None
#myNetatmo = None
#controller = None

#id = 'controller'
#drivers = [
#        {'driver': 'ST', 'value':0, 'uom':2},
#        ]

class NetatmoController(udi_interface.Node):
    from udiNetatmoLib import bool2ISY, prepare_node_adr, NET_setDriver, t_mode2ISY, node_queue, wait_for_node_done, con_state2ISY, convert_temp_unit, heartbeat
    from udiProfileUpdate import udiProfileUpdate
    def __init__(self, polyglot, primary, address, name):
        super(NetatmoController, self).__init__(polyglot, primary, address, name)
        logging.debug('NetatmoController Initializing')
        logging.setLevel(10)
        self.poly = polyglot

        self.id = 'controller'
        self.drivers =  [ {'driver': 'ST', 'value':0, 'uom':25}, ]
        self.accessTokenEn = True
        self.accessToken = None
        self.nodeDefineDone = False
        self.configDone = False
        self.name = name
        self.primary = primary
        self.address = address
        self.temp_unit = 0
        self.nodes_in_db = self.poly.getNodesFromDb()
        self.myNetatmo = NetatmoOauthHomeCtrl(self.poly, 'read_magellan write_magellan read_smarther write_smarther read_mhs1 write_mhs1')
        self.hb  = 0
        #logging.debug('testing 1')
        #self.customParameters = Custom(self.poly, 'customparams')
        self.Notices = Custom(self.poly, 'notices')
        self.n_queue = []
        #logging.debug('drivers : {}'.format(self.drivers))
        self.poly.subscribe(self.poly.STOP, self.stopHandler)
        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.myNetatmo.customParamsHandler)
        #self.poly.subscribe(self.poly.CUSTOMDATA, self.myNetatmo.customDataHandler)
        self.poly.subscribe(self.poly.CUSTOMNS, self.myNetatmo.customNsHandler)
        self.poly.subscribe(self.poly.OAUTH, self.myNetatmo.oauthHandler)
        self.poly.subscribe(self.poly.CONFIGDONE, self.configDoneHandler)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.subscribe(self.poly.POLL, self.systemPoll)


        self.home_list = []
        #logging.debug('testing 2')

        self.poly.addNode(self)
        #logging.debug('drivers : {}'.format(self.drivers))
        #logging.debug('testing 3')
        #self.wait_for_node_done()
        #logging.debug('testing 4')
        self.node = self.poly.getNode(self.address)
        #logging.debug('testing 5')
        self.nodes_in_db = self.poly.getNodesFromDb()
        self.poly.updateProfile()
        self.poly.ready()
       

       

    def start(self):
        logging.info('Executing start')
        #self.myNetatmo = NetatmoWeather(self.poly)
        #self.accessToken = self.myNetatmo.getAccessToken()
        #logging.debug('Waiting start: {} {} {}'.format(self.configDone, self.myNetatmo.customParamsDone(), self.myNetatmo.customNsDone()))
        while not (self.configDone and self.myNetatmo.customParamsDone() and self.myNetatmo.customNsDone()):
        #while not (self.configDone):
            time.sleep(2)
            logging.debug('Waiting for config to complete {} {} {}'.format(self.configDone, self.myNetatmo.customParamsDone(),  self.myNetatmo.customNsDone()))
        #time.sleep(1)
        #if self.refreshToken and self.client_ID and self.client_SECRET:
        #    self.myNetatmo._insert_refreshToken(self.refreshToken, self.client_ID, self.client_SECRET)
        #    logging.debug('AccessToken = {}'.format(self.accessToken))

            
        while not self.myNetatmo.authendicated():
            logging.warning('Access token is not yet available. Please authenticate.')
            self.poly.Notices['auth'] = 'Please initiate authentication'
            time.sleep(5)            

        
        time.sleep(1)
        self.poly.Notices.clear()    

        homes_dict = self.myNetatmo.get_homectrl_homes()
        if homes_dict:
            self.node.setDriver('ST', 1, True, True)
        logging.debug('Home ids: {}'.format(homes_dict))

        for home_id, home in homes_dict.items():
            logging.debug('home-id, home {} - {}'.format(home_id, home))
            if home['name'] not in self.myNetatmo.customParameters:
                self.myNetatmo.customParameters[home['name']] = 1
                self.home_list.append(home)
                logging.info('Adding {} to node new'.format(home['name']))                
            else:
                if self.myNetatmo.customParameters[home['name']] == 1:
                    self.home_list.append(home)
                    logging.info('Adding {} to node'.format(home['name']))
   
        self.temp_unit = self.convert_temp_unit(self.myNetatmo.temp_unit)
        logging.debug('TEMP_UNIT: {}'.format(self.temp_unit ))

        while not (self.myNetatmo.customParamsDone() and self.myNetatmo.customNsDone() and self.configDone):
            logging.info('Waiting for configuration to complete')
            time.sleep(1)
        #update data
        for home_id in self.home_list:
            self.myNetatmo.get_home_status(home_id)
            scenario_list = self.myNetatmo.get_homes_scenarios(home_id)
            #self.udiProfileUpdate(scenario_list)
        self.addNodes()
        self.wait_for_node_done()


    def addNodes(self):
        
        logging.info('Adding rooms of selected homes')
        selected = False
        #primary_gateway_list = ['NAPlug'] # controller is there for sure 
        node_adr_list = [self.id]
        for indx, home  in enumerate(self.home_list):
            logging.debug('Adding rooms  {}'.format(home))
            home_name = self.poly.getValidName(home['name'])
            if 'rooms' in home:
                for room_indx, room in enumerate(home['rooms']):
                    # check if control valve is on room:
                    device_found = False
                    logging.debug('Rooms {}'.format(room))
                    if 'module_ids' in room:
                        for mod_id, mod_adr in enumerate(room['module_ids']):
                            logging.debug('Parsing module IDs {} {}'.format(mod_id, mod_adr ))
                            if self.myNetatmo.isControlDevice(home, mod_adr):#'modules' in home:
                                device_found = True
                                node_adr_list.append(self.prepare_node_adr(mod_adr,14))
                                #for mod_idx, module in enumerate(home['modules']):                                                            
                                #    if module['id'] == mod_id and module['type'] in self._device_list:
                                #        device_found = True
                    if device_found:
                        room_name = self.poly.getValidName(room['name'])
                        node_name = home_name+'-'+room_name
                        room_node = 'room'+ self.prepare_node_adr(room['id'], 10)
                        node_address = self.poly.getValidAddress(room_node)
                        logging.debug('adding room node : {} {} {} {} {} {}'.format(node_address, node_address, node_name,  self.myNetatmo, home, room['id']))
                        if self.myNetatmo.room_has_energy(home, room['id']):
                            temp = udiNetatmoEnergyRoom(self.poly, node_address, node_address, node_name,  self.myNetatmo, home, room['id'])
                        else:
                            temp = udiNetatmoHomeCtrlRoom(self.poly, node_address, node_address, node_name,  self.myNetatmo, home, room['id'])
                        node_adr_list.append(node_address)
                        while not temp.node_ready:
                            logging.debug( 'Waiting for node {}-{} to be ready'.format(self.home_id, node_name))
                            time.sleep(1)
            
        #removing unused nodes

        while not self.configDone:
            logging.info('Waiting for config to comlete')
            time.sleep(1)
        logging.debug('Checking for nodes not used - node list {} - {} {}'.format(node_adr_list, len(self.nodes_in_db), self.nodes_in_db))
        for nde, node in enumerate(self.nodes_in_db):
            #node = self.nodes_in_db[nde]
            logging.debug('Scanning db for extra nodes : {}'.format(node))
            if node['primaryNode'] not in node_adr_list:
                logging.debug('Removing primary node : {} {}'.format(node['name'], node))
                self.poly.delNode(node['address'])
            elif node['address'] not in node_adr_list:
                logging.debug('Removing sub node : {} {}'.format(node['name'], node))
                self.poly.delNode(node['address'])

        self.nodeDefineDone = True

    def update_ISY_data(self):
        logging.info('update_ISY_data executing:')
        nodes = self.poly.nodes()
        for nde in nodes:
            if nde.address != 'controller':   # but not the setup node
                logging.debug('updating node {} data'.format(nde))
                nde.updateISYdrivers()

    def configDoneHandler(self):
        # We use this to discover devices, or ask to authenticate if user has not already done so
        self.poly.Notices.clear()
        logging.info('configDoneHandler called')
        #self.myNetatmo.updateOauthConfig()
        self.nodes_in_db = self.poly.getNodesFromDb()
        logging.debug('Nodes in Nodeserver - before cleanup: {} - {}'.format(len(self.nodes_in_db),self.nodes_in_db))
        self.configDone = True
        
        #res = self.myNetatmo.get_home_info()
        #logging.debug('retrieved get_home_info data {}'.format(res))

        #res = self.myNetatmo.get_weather_info()
        #logging.debug('retrieved get_weather_info data {}'.format(res))

        #res = self.myNetatmo.get_weather_info2()
        #logging.debug('retrieved get_weather_info2 data2 {}'.format(res))

        #self.poly.discoverDevices()

    def update(self, command):
        self.updateISYdrivers()
              
    def updateISYdrivers(self):
        try:
            self.node.setDriver('ST', 1, True, True)
        except Exception:
            logging.error('eISY/Polisy aopears offline')
            self.node.setDriver('ST', 0, True, True)

    def updateEnergy(self):
        pass

    def systemPoll (self, polltype):
        #if self.nodeDefineDone:
        logging.info('System Poll executing: {}'.format(polltype))
        nodes = self.poly.nodes()
        if nodes:
        #logging.debug('nodes : {}'.format(nodes))
            try:
                if 'longPoll' in polltype:
                    #Keep token current
                    #self.node.setDriver('GV0', self.temp_unit, True, True)
                    
                    #self.myNetatmo.refresh_token()
                    self.myNetatmo.get_homes_info()
                    for home_id in self.myNetatmo.homes_list:
                        self.myNetatmo.get_home_status(self.myNetatmo.homes_list[home_id])


                        #self.myNetatmo.update_weather_info_instant(home)
                    #nodes = self.poly.getNodes()
                    for nde in nodes:
                        if nde.address != 'controller':   # but not the setup node
                            logging.debug('updating node {} data'.format(nde))
                            nde.updateISYdrivers()
                            nde.updateEnergy()
                                                
                if 'shortPoll' in polltype:
                    self.heartbeat()
                    #self.myNetatmo.refresh_token()
                    logging.debug('shortpoll  {}'.format(self.myNetatmo.homes_list))
                    for home_id in self.myNetatmo.homes_list:
                        logging.debug('shortpoll loop {}'.format(self.myNetatmo.homes_list[home_id]))
                        self.myNetatmo.get_home_status(self.myNetatmo.homes_list[home_id])
                    for nde in nodes:
                        if nde.address != 'controller':   # but not the setup node
                            logging.debug('updating node {} data'.format(nde))
                            nde.updateISYdrivers()
            except Exception as e:
                    logging.error('Exeption occcured : {}'.format(e))
    
                
        #else:
        #    logging.info('System Poll - Waiting for all nodes to be added')
 

    def stopHandler(self):
        # Set nodes offline
        for node in self.poly.nodes():
            if hasattr(node, 'setOffline'):
                #node.setDriver('ERR', 1)
                node.setOffline()
        self.poly.stop()
        
    commands = {        
                    'UPDATE'    : update,
    }

if __name__ == "__main__":
    try:
        logging.info ('starting')
        logging.info('Starting Netatmo Controller')
        polyglot = udi_interface.Interface([])
        #polyglot.start('0.2.31')

        polyglot.start({ 'version': version, 'requestId': True })

        # Show the help in PG3 UI under the node's Configuration option
        polyglot.setCustomParamsDoc()

        # Update the profile files
        #polyglot.updateProfile()

        # Implements the API calls & Handles the oAuth authentication & token renewals
        #myNetatmo = NetatmoWeather(polyglot)

        # then you need to create the controller node
        NetatmoController(polyglot, 'controller', 'controller', 'Netatmo Home')

        # subscribe to the events we want
        # polyglot.subscribe(polyglot.POLL, pollHandler)

        # We can start receive events
        polyglot.ready()

        # Just sit and wait for events
        polyglot.runForever()

    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)

    except Exception:
        logging.error(f"Error starting Nodeserver: {traceback.format_exc()}")
        polyglot.stop()



