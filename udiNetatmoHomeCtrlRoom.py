#!/usr/bin/env python3

"""
Polyglot v3 node server
Copyright (C) 2023 Universal Devices

MIT License
"""

import time


try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)


from udiNetatmoHomeCtrlDevices import udiNetatmoSwitch


#from udi_interface import logging, Custom, Interface
#id = 'main_netatmo'



class udiNetatmoHomeCtrlRoom(udi_interface.Node):
    from udiNetatmoLib import bool2ISY, t_mode2ISY, update_ISY_data,  node_queue, wait_for_node_done, con_state2ISY, convert_temp_unit, ISY2sp_mode, ISY2op_mode
    def __init__(self, polyglot, primary, address, name, myNetatmo, home, room_id):
        super().__init__(polyglot, primary, address, name)

        self.poly = polyglot
        self.myNetatmo = myNetatmo
        self._home = home
        self.home_id = home['id']
        self.room_id = room_id
        self.node_ready = False
        self.n_queue = []
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        #self.module = {'module_id':module_info['main_module'], 'type':'MAIN', 'home_id':module_info['home'] }
        #logging.debug('self.module = {}'.format(self.module))
        self.id = 'room'
        self.drivers = [
            {'driver' : 'CLITEMP', 'value': 99,  'uom':25}, 
            {'driver' : 'CLISPH', 'value': 99,  'uom':25}, 
            {'driver' : 'CLIMD', 'value': 99,  'uom':25}, 
            {'driver' : 'GV0', 'value': 99,  'uom':25}, 
            {'driver' : 'GV1', 'value': 0,  'uom':2}, 
            {'driver' : 'GV2', 'value': 0,  'uom':2}, 
            {'driver' : 'GV3', 'value': 99,  'uom':25},      
            {'driver' : 'ST', 'value': 99,  'uom':25}, 
            ]
        self.primary = primary
        self.address = address
        self.name = name

        #self.myNetatmo = NetatmoWeather
        #self.home_id = module_info['home']
        #self.main_module_id = module_info['main_module']

        self.Parameters = Custom(self.poly, 'customparams')
        self.Notices = Custom(self.poly, 'notices')
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.STOP, self.stop)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)

        polyglot.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node_ready = True
        self.node = self.poly.getNode(address)
        logging.info('Start {} room Node'.format(self.name))  
        time.sleep(1)

       

    


    def start(self):
        logging.debug('Executing udiNetatmoEnergyRoom start')
        self.addNodes()
        self.updateISYdrivers()

    def stop (self):
        pass
    
    def addNodes(self):
        '''addNodes'''

        logging.debug('Adding valves to {} {}'.format(self.name, self._home))

        if 'modules' in self._home:
            for indx in range(0, len(self._home['modules'])):
                valve_info = self._home['modules'][indx]
                logging.debug('Valve check {} {}'.format( self.room_id, valve_info))
                if valve_info['room_id'] == self.room_id and valve_info['type'] == 'NRV':
                    valve_name = valve_info['name']
                    node_name = self.poly.getValidName(valve_name)
                    valve_id = valve_info['id']
                    node_address = self.poly.getValidAddress(valve_id)
                    logging.debug('adding valve node : {} {} {} {} {} {}'.format( self.primary, node_address, node_name, self.myNetatmo, self._home,  valve_id))

                    tmp_room = udiNetatmoSwitch(self.poly, self.primary, node_address, node_name, self.myNetatmo, self._home,  valve_id)
                    while not tmp_room.node_ready:
                        logging.debug( 'Waiting for node {}-{} to be ready'.format(valve_id, node_name))
                        time.sleep(4)



                
    def update(self, command = None):
        logging.debug('update room data {}'.format(self._home))
        self.myNetatmo.get_home_status(self._home['id'])
        #self.myNetatmo.update_weather_info_instant(self.module['home_id'])
        self.update_ISY_data()

   
        
    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')
        #data = self.myNetatmo.get_module_data(self.module)
        #logging.debug('Main module data: {}'.format(data))
        if self.node is not None:

            if self.myNetatmo.get_room_online(self.home_id, self.room_id):
                self.node.setDriver('ST', 1)
                logging.debug('TempUnit = {} {}'.format(self.myNetatmo.temp_unit, self.convert_temp_unit(self.myNetatmo.temp_unit)))
                if self.convert_temp_unit(self.myNetatmo.temp_unit) == 0:
                    self.node.setDriver('CLITEMP', round(self.myNetatmo.get_room_temp(self.home_id, self.room_id),1), True, False, 4 )
                    self.node.setDriver('CLISPH', round(int(self.myNetatmo.get_room_setpoint_temp(self.home_id, self.room_id)*2)/2,1), True, False, 4 )
                else:
                    self.node.setDriver('CLITEMP', round(int(2*(self.myNetatmo.get_room_temp(self.home_id, self.room_id)*9/5+32))/2,1), True, False, 17 )
                    self.node.setDriver('CLISPH', round(int(2*(self.myNetatmo.get_room_setpoint_temp(self.home_id, self.room_id)*9/5+32))/2,0), True, False, 17 )
                self.node.setDriver('CLIMD', self.t_mode2ISY(self.myNetatmo.get_room_setpoint_mode(self.home_id, self.room_id)))
                self.node.setDriver('GV0', self.myNetatmo.get_room_heat_power_request(self.home_id, self.room_id), True, False, 0)
                self.node.setDriver('GV1', self.bool2ISY(self.myNetatmo.get_room_open_window(self.home_id, self.room_id)))
                self.node.setDriver('GV2', self.bool2ISY(self.myNetatmo.get_room_anticipating(self.home_id, self.room_id)))
                self.node.setDriver('GV3', int(self.myNetatmo.get_time_since_last_update_sec(self.home_id)/60), True, True, 44)
 
            else:
                self.node.setDriver('CLITEMP', 99, True, False, 25 )
                self.node.setDriver('CLISPH', 99, True, False, 25 )
                self.node.setDriver('CLIMD', 99, True, False, 25 )
                self.node.setDriver('GV0', 99, True, False, 25 )
                self.node.setDriver('GV1', 99, True, False, 25 )
                self.node.setDriver('GV2', 99, True, False, 25 )
                self.node.setDriver('GV3', 99, True, False, 25 )
                self.node.setDriver('ST', 0) 




    def set_setpoint(self, command):
        #{'address': 'room3956476596', 'cmd': 'SETPOINT', 'query': {'stemp.uom17': '44.6', 'mode.uom25': '0', 'active_t.uom44': '0'}}
        logging.debug('set_set_point {} called'.format(command))
        t_stop = 0
        query = command.get('query')
        if 'stemp.uom17' in query:
            Ftemp = float(query.get('stemp.uom17'))
            Ctemp = round((Ftemp - 32)*5/9, 0)
            #logging.debug('F 2 Celcius {}  {}'.format(Ftemp, Ctemp))
        elif 'stemp.uom4' in query:    
            Ctemp = round(int(float(query.get('stemp.uom4'))*2)/2,1)
            #logging.debug('Celcius {}'.format(Ctemp))
        else:
            logging.error('something went wrong in set_setpoint {}'.format(query))
        mode = self.ISY2sp_mode(int(query.get('spmode.uom25')))
        active_min = int(query.get('active_t.uom44'))
        if active_min != 0:
            t_now = int(time.time())
            t_stop = t_now + 60*active_min
            logging.debug('time : {} {}'.format(t_now, t_stop))            
        res = self.myNetatmo.execute_set_setpoint(self.home_id, self.room_id, Ctemp, mode, t_stop)
        try:
            if res['status'] == 'ok':
                self.update()
        except:
            logging.error('set_setpoint failed')  

    def set_opmode(self, command):
        # {'address': 'room3956476596', 'cmd': 'OPMODE', 'value': '1', 'uom': '25', 'query': {}}
        logging.debug('set_opmode {} called'.format(command))
        t_stop = 0
        query = command.get('query')
        mode = self.ISY2op_mode( int(query.get('opmode.uom25')))
        active_min = int(query.get('active_t.uom44'))
        if active_min != 0:
            t_now = int(time.time())
            t_stop = t_now + 60*active_min
            logging.debug('time : {} {}'.format(t_now, t_stop))
        res = self.myNetatmo.execute_set_mode(self.home_id, mode, t_stop)
        try:
            if res['status'] == 'ok':
                self.update()
        except:
            logging.error('set_opmode failed')    

    commands = {        
                'UPDATE'    : update,
                'SETPOINT'  : set_setpoint,
                'OPMODE'    : set_opmode,
                }

        
