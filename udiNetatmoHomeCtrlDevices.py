#!/usr/bin/env python3

"""
Polyglot v3 node server
Copyright (C) 2023 Universal Devices

MIT License
"""


import time
import traceback
import re

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)


#from nodes.controller import Controller
#from udi_interface import logging, Custom, Interface
class udiNetatmoPower(udi_interface.Node):
    from udiNetatmoLib import bool2ISY, t_mode2ISY, NET_setDriver, on_state2ISY, update_ISY_data, node_queue, wait_for_node_done, battery2ISY, con_state2ISY

    def __init__(self, polyglot, primary, address, name, myNetatmo, home,  module_id):
        super().__init__(polyglot, primary, address, name)
        logging.debug('__init__ udiNetatmoPower {} {} {} {} {}'.format(primary, address,name, home, module_id  ))
        self.poly = polyglot
        self.myNetatmo= myNetatmo
        self.module_id = module_id
        self.home_id = home['id']
        self._home = home
        self.primary = primary
        self.address = address
        self.name = name        
        self.n_queue = []
        self.id = 'power'
        self.drivers = [

            {'driver' : 'GV0', 'value': 99,  'uom':25}, 
            {'driver' : 'GV2', 'value': 99,  'uom':25}, 
            {'driver' : 'GV1', 'value': 99,  'uom':25},       
            {'driver' : 'ST', 'value': 99,  'uom':25}, 
            ]

        self.node_ready = False
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.STOP, self.stop)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        logging.info('Start {} Power Node'.format(self.name))  
        time.sleep(1)
        self.nodeDefineDone = True
        self.node_ready = True

    def start(self):
        logging.debug('Executing udiNetatmoPower start')
        self.updateISYdrivers()     
        self.updateEnergy()

    def updateEnergy(self):
        self.myNetatmo.get_energy_kwh(self.home_id, self.module_id)

    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')

        #data = self.myNetatmo.get_module_data(self.module)
        logging.debug('Power module data:')
        if self.node is not None:
            if self.myNetatmo.get_module_online(self.home_id, self.module_id):
                self.NET_setDriver('ST',1)
                self.NET_setDriver('GV0', self.on_state2ISY(self.myNetatmo.get_state(self.home_id, self.module_id)))
                self.NET_setDriver('GV1', int(-self.myNetatmo.get_power_used(self.home_id, self.module_id)),  51)
                
    def outlet_control(self, command):
        logging.debug('outlet_control called {}'.format(command))
        on_off = int(command.get('value'))
        logging.debug('Command data : {}'.format(on_off == 1))
        if self.myNetatmo.set_state(self.home_id, self.module_id, on_off == 1):
            self.NET_setDriver('GV0',on_off == 1)
        else:
            self.NET_setDriver('GV0', 99)

    def update(self, command = None):
        self.myNetatmo.get_home_status(self._home['id'])
        self.update_ISY_data()       


    commands = {        
                'UPDATE': update,
                'OUTLETCTRL' : outlet_control
              }

class udiNetatmoRemote(udi_interface.Node):
    from udiNetatmoLib import bool2ISY, t_mode2ISY, NET_setDriver, update_ISY_data, node_queue, wait_for_node_done, battery2ISY, con_state2ISY

    def __init__(self, polyglot, primary, address, name, myNetatmo, home,  module_id):
        super().__init__(polyglot, primary, address, name)
        logging.debug('__init__ udiNetatmoRemote {} {} {} {} {}'.format(primary, address,name, home, module_id  ))
        self.poly = polyglot
        self.myNetatmo= myNetatmo
        self.module_id = module_id
        self.home_id = home['id']
        self._home = home
        self.primary = primary
        self.address = address
        self.name = name        
        self.n_queue = []
        self.id = 'remote'
        self.drivers = [

            {'driver' : 'GV0', 'value': 99,  'uom':25},
            {'driver' : 'GV2', 'value': 99,  'uom':25},
            {'driver' : 'ST', 'value': 99,  'uom':25},
            ]

        self.node_ready = False
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.STOP, self.stop)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        logging.info('Start {} Remote Node'.format(self.name))  
        time.sleep(1)
        self.nodeDefineDone = True
        self.node_ready = True


    def start(self):
        logging.debug('Executing udiNetatmoRemote start')
        self.updateISYdrivers()        


    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')

        #data = self.myNetatmo.get_module_data(self.module)
        logging.debug('Remotes module data:')
        if self.node is not None:
            if self.myNetatmo.get_module_online(self.home_id, self.module_id):
                self.NET_setDriver('ST',1)
                self.NET_setDriver('GV2', round(self.myNetatmo.get_valve_bat_level(self.home_id, self.module_id)/1000, 2), 72)
                self.NET_setDriver('GV0', self.battery2ISY(self.myNetatmo.get_valve_bat_state(self.home_id, self.module_id)))

    def updateEnergy(self):
        pass

class udiNetatmoGateway(udi_interface.Node):
    from udiNetatmoLib import bool2ISY, t_mode2ISY, NET_setDriver, update_ISY_data, node_queue, wait_for_node_done, battery2ISY, con_state2ISY

    def __init__(self, polyglot, primary, address, name, myNetatmo, home,  module_id):
        super().__init__(polyglot, primary, address, name)
        logging.debug('__init__ udiNetatmoGateway {} {} {} {} {}'.format(primary, address,name, home, module_id ))
        self.poly = polyglot
        self.myNetatmo= myNetatmo
        self.module_id = module_id
        self.home_id = home['id']
        self._home = home
        self.primary = primary
        self.address = address
        self.name = name        
        self.n_queue = []
        self.id = 'gateway'
        self.drivers = [

            {'driver' : 'GV10', 'value': 99,  'uom':25},
            {'driver' : 'ST', 'value': 99,  'uom':25},
            ]

        self.node_ready = False
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.STOP, self.stop)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        logging.info('Start {} Remote Node'.format(self.name))  
        time.sleep(1)
        self.nodeDefineDone = True
        self.node_ready = True


    def start(self):
        logging.debug('Executing udiNetatmoRemote start')
        self.updateISYdrivers()        


    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')

        #data = self.myNetatmo.get_module_data(self.module)
        logging.debug('Remotes module data:')
        if self.node is not None:
            if self.myNetatmo.get_module_online(self.home_id, self.module_id):
                self.NET_setDriver('ST',1)
                self.NET_setDriver('GV10', self.myNetatmo.get_wifi_strength(self.home_id, self.module_id))

    def updateEnergy(self):
        pass


    def execute_scenario(self, command):
        #cmd = command#query = command.get("query")
        #unit = command.get('uom')
        indx = str(command.get('value'))
        if len(self.myNetatmo.home_scenarios[self.home_id]) >= indx:
            scenario = self.myNetatmo.home_scenarios[self.home_id][indx]
            self.myNetatmo.launch_scenario(self.home_id, self.module_id, scenario)
        self.update_ISY_data()

    def update(self, command = None):
        self.myNetatmo.get_home_status(self._home['id'])
        self.update_ISY_data()

    commands = {        
                'UPDATE': update,
                'SCENARIO' : execute_scenario,
              }


class udiNetatmoLights(udi_interface.Node):
    from udiNetatmoLib import bool2ISY, t_mode2ISY, NET_setDriver, on_state2ISY, update_ISY_data, node_queue, wait_for_node_done, battery2ISY, con_state2ISY

    def __init__(self, polyglot, primary, address, name, myNetatmo, home,  module_id):
        super().__init__(polyglot, primary, address, name)
        logging.debug('__init__ udiNetatmoLights {} {} {} {} {}'.format(primary, address,name, home, module_id ))
        self.poly = polyglot
        self.myNetatmo= myNetatmo
        self.module_id = module_id
        self.home_id = home['id']
        self._home = home
        self.primary = primary
        self.address = address
        self.name = name        
        self.n_queue = []
        self.id = 'switch'
        self.drivers = [

            {'driver' : 'GV0', 'value': 99, 'uom':25}, 
            {'driver' : 'GV1', 'value': 99, 'uom':25},       
            {'driver' : 'ST', 'value': 99,  'uom':25}, 
            ]

        self.node_ready = False
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.STOP, self.stop)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        logging.info('Start {} Lights Node'.format(self.name))  
        time.sleep(1)
        self.n_queue = []  
        self.nodeDefineDone = True
        self.node_ready = True


    def start(self):
        logging.debug('Executing udiNetatmoLights start')
        self.updateISYdrivers()        
        self.updateEnergy()


    def updateEnergy(self):
        self.myNetatmo.get_energy_kwh(self.home_id, self.module_id)
   
        
    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')

        #data = self.myNetatmo.get_module_data(self.module)
        logging.debug('Lighth module data:')
        if self.node is not None:
            if self.myNetatmo.get_module_online(self.home_id, self.module_id):
                self.NET_setDriver('ST',1)
                self.NET_setDriver('GV0', self.os_state2ISY(self.myNetatmo.get_state(self.home_id, self.module_id)))
                self.NET_setDriver('GV1', int(self.myNetatmo.get_brightness(self.home_id, self.module_id)),  51)
                
    def brightness_control(self, command):
        logging.debug('brightness_control called {}'.format(command))

        brightness = int(command.get('value'))
        logging.debug('Command data : {}'.format(brightness))
        if self.myNetatmo.set_brightness(self.home_id, self.module_id, brightness):
            self.NET_setDriver('GV1', brightness)
        else:
            self.NET_setDriver('GV1', 99)

    def light_control(self, command):
        logging.debug('light_control called {}'.format(command))
        on_off = int(command.get('value'))
        logging.debug('Command data : {}'.format(on_off == 1))
        if self.myNetatmo.set_state(self.home_id, self.module_id, on_off == 1):
            self.NET_setDriver('GV0',on_off == 1)
        else:
            self.NET_setDriver('GV0', 99)

    def update(self, command = None):
        self.myNetatmo.get_home_status(self._home['id'])
        self.update_ISY_data()

    commands = {        
                'UPDATE': update,
                'BRIGHTCTRL' : brightness_control,
                'LIGHTCTRL' : light_control,
              }

'''
class udiNetatmoValve(udi_interface.Node):
    from udiNetatmoLib import bool2ISY, t_mode2ISY, NET_setDriver, update_ISY_data, node_queue, wait_for_node_done, battery2ISY, con_state2ISY

    def __init__(self, polyglot, primary, address, name, myNetatmo, home,  module_id):
        super().__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.myNetatmo= myNetatmo
        self.module_id = module_id
        self.home_id = home['id']
        self._home = home
        self.primary = primary
        self.address = address
        self.name = name        
        self.n_queue = []
        self.id = 'valve'
        self.drivers = [

            {'driver' : 'GV0', 'value': 99,  'uom':25}, 
            {'driver' : 'GV2', 'value': 99,  'uom':25}, 
            {'driver' : 'GV1', 'value': 99,  'uom':25},       
            {'driver' : 'ST', 'value': 99,  'uom':25}, 
            ]

        self.node_ready = False
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.STOP, self.stop)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        logging.info('Start {} valve Node'.format(self.name))  
        time.sleep(1)
        self.n_queue = []  
        self.nodeDefineDone = True
        self.node_ready = True

    
    


    def start(self):
        logging.debug('Executing udiNetatmoValve start')
        self.updateISYdrivers()        


   
        
    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')

        #data = self.myNetatmo.get_module_data(self.module)
        logging.debug('Valve module data:')
        if self.node is not None:
            if self.myNetatmo.get_valve_online(self.home_id, self.module_id):
                self.NET_setDriver('ST',1)
                self.NET_setDriver('GV2', round(self.myNetatmo.get_valve_bat_level(self.home_id, self.module_id)/1000, 2), 72)
                self.NET_setDriver('GV0', self.battery2ISY(self.myNetatmo.get_valve_bat_state(self.home_id, self.module_id)))
                self.NET+setDriver('GV1', int(-self.myNetatmo.get_valve_rf_strength(self.home_id, self.module_id)), True, True, 131)

                

    def update(self, command = None):
        self.myNetatmo.get_home_status(self._home['id'])
        self.update_ISY_data()


    commands = {        
                'UPDATE': update,
              }


class udiNetatmoThermostat(udi_interface.Node):
    from udiNetatmoLib import bool2ISY, t_mode2ISY, update_ISY_data, node_queue, wait_for_node_done, battery2ISY, con_state2ISY

    def __init__(self, polyglot, primary, address, name, myNetatmo, home,  module_id):
        super().__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.myNetatmo= myNetatmo
        self.module_id = module_id
        self.home_id = home['id']
        self._home = home
        self.primary = primary
        self.address = address
        self.name = name        
        self.n_queue = []
        self.id = 'valve'
        self.drivers = [

            {'driver' : 'GV0', 'value': 99,  'uom':25}, 
            {'driver' : 'GV2', 'value': 99,  'uom':25}, 
            {'driver' : 'GV1', 'value': 99,  'uom':25},       
            {'driver' : 'ST', 'value': 99,  'uom':25}, 
            ]

        self.node_ready = False
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.STOP, self.stop)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        logging.info('Start {} valve Node'.format(self.name))  
        time.sleep(1)
        self.n_queue = []  
        self.nodeDefineDone = True
        self.node_ready = True

    
    


    def start(self):
        logging.debug('Executing udiNetatmoThermostat start')
        self.updateISYdrivers()        


   
        
    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')

        #data = self.myNetatmo.get_module_data(self.module)
        logging.debug('Thermostat module data:')
        if self.node is not None:
            if self.myNetatmo.get_valve_online(self.home_id, self.module_id):
                self.node.setDriver('ST',1)
                #self.node.setDriver('GV2', round(self.myNetatmo.get_valve_bat_level(self.home_id, self.module_id)/1000, 2), True, True, 72)
                #self.node.setDriver('GV0', self.battery2ISY(self.myNetatmo.get_valve_bat_state(self.home_id, self.module_id)))
                self.node.setDriver('GV1', int(-self.myNetatmo.get_valve_rf_strength(self.home_id, self.module_id)), True, True, 131)
            else:
                self.node.setDriver('GV2', 99, True, False, 25 )
                self.node.setDriver('GV0', 99)
                self.node.setDriver('GV1', 99, True, False, 25 )
                self.node.setDriver('ST', 0)
                

    def update(self, command = None):
        self.myNetatmo.get_home_status(self._home['id'])
        self.update_ISY_data()


    commands = {        
                'UPDATE': update,
              }
    '''              