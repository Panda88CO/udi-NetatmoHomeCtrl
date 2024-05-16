
#!/usr/bin/env python3

### Your external service class
'''
Your external service class can be named anything you want, and the recommended location would be the lib folder.
It would look like this:

External service sample code
Copyright (C) 2023 Universal Devices

MIT License
'''
import requests
import time
import urllib.parse
from datetime import datetime, timezone
#from udi_interface import LOGGER, Custom
from NetatmoOauth import NetatmoCloud
try:
    from udi_interface import LOGGER, Custom, OAuth
    logging = LOGGER
    Custom = Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)



# Implements the API calls to your external service
# It inherits the OAuth class
class NetatmoOauthHomeCtrl(NetatmoCloud):
    yourApiEndpoint = 'https://api.netatmo.com/api'

    def __init__(self, polyglot, scope):
        super().__init__(polyglot, scope)
        logging.info('OAuth initializing')
        self.poly = polyglot
        self.scope = scope
        self.customParameters = Custom(self.poly, 'customparams')
        #self.scope_str = None
        self.apiEndpoint = 'https://api.netatmo.com'
        self.client_ID = None
        self.client_SECRET = None
        self.handleCustomParamsDone = False
        #self.customerDataHandlerDone = False
        self.customNsHandlerDone = False
        self.temp_unit = 'C'

        self.scopeList = [ 'read_magellan', 'write_magellan', 'read_smarther', 'write_smarther', 'read_mhs1', 'write_mhs1', 'read_thermostat', 'write_thermostat']
        
        self._dev_list  = ['NAPlug', 'NRV', 'NATherm1']

        self.energy_data = {}
        self.GW_modules = ['NAPlug', 'NLG', 'NLGS', 'NLE']

        self.power_list =['NLP', 'NLPS']
        self.lights_list = ['NLF']
        self.remotes_list = ['NLT']

        self.thermostat_list = ['NATherm1']
        self.valves_list = ['NRV']
        


        self._dev_list  = self.power_list+self.lights_list+self.remotes_list
        logging.debug('_dev_list: {}'.format(self._dev_list))
        #self.customParameters= Custom(polyglot, 'customparams')
        #self.Notices = Custom(self.poly, 'notices')

        logging.info('External service connectivity initialized...')
        #logging.debug('oauth : {}'.format(self.oauthConfig))

        time.sleep(1)
        #while not self.handleCustomParamsDone:
        #    logging.debug('Waiting for customParams to complete - getAccessToken')
        #    time.sleep(0.2)
        # self.getAccessToken()
    
    # The OAuth class needs to be hooked to these 3 handlers
    def customDataHandler(self, data):
        logging.debug('customDataHandler called')
        #while not self.handleCustomParamsDone:
        #    logging.debug('Waiting for customDataHandler to complete')
        #    time.sleep(1)
        super().customDataHandler(data)
        self.customDataHandlerDone = True
        logging.debug('customDataHandler Finished')

    def customNsHandler(self, key, data):
        logging.debug('customNsHandler called')
        #while not self.customParamsDone():
        #    logging.debug('Waiting for customNsHandler to complete')
        #    time.sleep(1)
        #self.updateOauthConfig()
        super().customNsHandler(key, data)
        self.customNsHandlerDone = True
        logging.debug('customNsHandler Finished')

    def oauthHandler(self, token):
        logging.debug('oauthHandler called')
        while not (self.customParamsDone() and self.customNsDone()):
            logging.debug('Waiting for oauthHandler to complete')
            time.sleep(5)
        super().oauthHandler(token)
        self.customOauthHandlerDone = True
        logging.debug('oauthHandler Finished')

    def customNsDone(self):
        return(self.customNsHandlerDone)
    
    def customDateDone(self):
        return(self.customDataHandlerDone )

    def customParamsDone(self):
        return(self.handleCustomParamsDone)
    #def refresh_token(self):
    #    logging.debug('checking token for refresh')
        

    # Your service may need to access custom params as well...
    
    def main_module_enabled(self, node_name):
        logging.debug('main_module_enabled called {}'.format(node_name))
        if node_name in self.customParameters:           
            return(int(self.customParameters[node_name]) == 1)
        else:
            self.customParameters[node_name] = 1 #add and enable by default
            self.poly.Notices['home_id'] = 'Check config to select which home/modules should be used (1 - used, 0 - not used) - then restart'
            return(True)

                
    def customParamsHandler(self, userParams):
        self.customParameters.load(userParams)
        logging.debug('customParamsHandler called {}'.format(userParams))
        client_ok = False
        client_secret = False
        oauthSettingsUpdate = {}
        # Example for a boolean field

        if 'clientID' in userParams:
            if self.customParameters['clientID'] != 'enter client_id':
                self.client_ID = self.customParameters['clientID']
                oauthSettingsUpdate['client_id'] = self.customParameters['clientID']
                client_ok = True
        else:
            logging.warnig('No clientID found')
            self.customParameters['clientID'] = 'enter client_id'
            self.client_ID = None
            
        if 'clientSecret' in self.customParameters:
            if self.customParameters['clientSecret'] != 'enter client_secret':
                self.client_SECRET = self.customParameters['clientSecret'] 
                oauthSettingsUpdate['client_secret'] = self.customParameters['clientSecret']
                secret_ok = True
        else:
            logging.warnig('No clientSecret found')
            self.customParameters['clientSecret'] = 'enter client_secret'
            self.client_SECRET = None

        if not client_ok  or not secret_ok:
            self.poly.Notices['client'] = 'Please enter valid clientID and clientSecret - then restart'

        if "TEMP_UNIT" in self.customParameters:
            self.temp_unit = self.customParameters['TEMP_UNIT'][0].upper()
        else:
            self.temp_unit = 0
            self.customParameters['TEMP_UNIT'] = 'C'

        #if 'refresh_token' in self.customParameters:
        #    if self.customParameters['refresh_token'] is not None and self.customParameters['refresh_token'] != "":
        #        self.customData.token['refresh_token'] = self.customParameters['refresh_token']
        oauthSettingsUpdate['scope'] = self.scope
        oauthSettingsUpdate['auth_endpoint'] = 'https://api.netatmo.com/oauth2/authorize'
        oauthSettingsUpdate['token_endpoint'] = 'https://api.netatmo.com/oauth2/token'
        #oauthSettingsUpdate['cloudlink'] = True
        oauthSettingsUpdate['addRedirect'] = True
        self.updateOauthSettings(oauthSettingsUpdate)    
        #logging.debug('Updated oAuth config: {}'.format(self.getOauthSettings()))
        if client_ok and secret_ok:
            self.handleCustomParamsDone = True
            self.poly.Notices.clear()

        #self.updateOauthConfig()
        #self.myParamBoolean = ('myParam' in self.customParametersand self.customParameters['myParam'].lower() == 'true')
        #logging.info(f"My param boolean: { self.myParamBoolean }")
    

    def add_to_parameters(self,  key, value):
        '''add_to_parameters'''
        self.customParameters[key] = value

    def check_parameters(self, key, value):
        '''check_parameters'''
        if key in self.customParameters:
            return(self.customParameters[key]  == value)
        else:
            return(False)
    

    # Then implement your service specific APIs

### Main node server code

    #def set_temp_unit(self, value):
    #    self.temp_unit = value
#POST "https://api.netatmo.com/api/setroomthermpoint?home_id=1&room_id=2&mode=manual&temp=21&endtime=123"
    def execute_set_setpoint(self, home_id, room_id, Ctemp, mode, t_stop=0):
        logging.debug('execute_setpoint {} {} {}'.format( Ctemp, mode, t_stop))
        home_id_str = urllib.parse.quote_plus(home_id)
        room_id_str = urllib.parse.quote_plus(room_id)
        if mode == 'manual':
            api_str = '/setroomthermpoint?home_id='+home_id_str+'&room_id='+room_id_str+'&mode=manual'+'&temp='+str(Ctemp)
            if t_stop != 0: # do not add stop time 
                api_str=api_str+'&endtime='+str(int(t_stop))
        elif mode == 'max':
            api_str = '/setroomthermpoint?home_id='+home_id_str+'&room_id='+room_id_str+'&mode=max'
            if t_stop == 0: # do not add stop time 
                logging.warning('Warning no stop time specified - setting to 3 hours ')                
                t_stop = int(time.time()+3*60*50)                
            api_str=api_str+'&endtime='+str(int(t_stop))
        else:
            api_str = '/setroomthermpoint?home_id='+home_id_str+'&room_id='+room_id_str+'&mode=home'
            if t_stop != 0: # do not add stop time 
                api_str=api_str+'&endtime='+str(int(t_stop))            
        temp = self._callApi('POST', api_str )
        #logging.debug('execute_set_setpoint return: {} - {}'.format(api_str, temp))
        return(temp)

#POST "https://api.netatmo.com/api/setthermmode?home_id=12345&mode=away&endtime=12345"
    def execute_set_mode(self, home_id, mode, t_stop=0):
        logging.debug('execute_set_mode {} {}'.format( mode, t_stop))
        home_id_str = urllib.parse.quote_plus(home_id)
        api_str = '/setthermmode?home_id='+home_id_str+'&mode='+mode
        if t_stop != 0 and (mode == 'away' or mode == 'hg' ):
            api_str = api_str + '&endtime='+str(int(t_stop))
        temp = self._callApi('POST', api_str )
        logging.debug('execute_set_mode return: {} - {}'.format(api_str, temp))
        return(temp)


    '''
    

    def module_type (self, type):
        if type in self.GW_modules:
            return('GATEWAY')
        if type in self.valves:
            return('VALVE')
        if type in self.thermostat:
            return('THERMOSTAT')
              
    def get_time_since_last_update_sec(self, home_id):
        timenow = int(time.time())
        delay_s = int(timenow - self.energy_data[home_id]['meas_time'])
        return(delay_s)
    

    
    def get_room_temp(self, home_id, room_id):
        logging.debug('get_room_temp')
        if room_id in self.energy_data[home_id]['rooms']:
            return( self.energy_data[home_id]['rooms'][room_id]['therm_measured_temperature'])
        else:
            return(None)
        
    def get_room_setpoint_temp(self, home_id, room_id):
        logging.debug('get_room_set_point_temp')
        if room_id in self.energy_data[home_id]['rooms']:
            return( self.energy_data[home_id]['rooms'][room_id]['therm_setpoint_temperature'])
        else:
            return(None)


    def get_room_setpoint_mode(self, home_id, room_id):
        logging.debug('get_room_set_point_mode')
        if room_id in self.energy_data[home_id]['rooms']:
            return( self.energy_data[home_id]['rooms'][room_id]['therm_setpoint_mode'])
        else:
            return(None)
        
    def get_room_online(self, home_id, room_id):
        logging.debug('get_room_online - {} {} {}'.format(home_id, room_id, self.energy_data))
        if room_id in self.energy_data[home_id]['rooms']:
            return( self.energy_data[home_id]['rooms'][room_id]['reachable'])
        else:
            return(None)
    
    def get_room_anticipating(self, home_id, room_id):
        logging.debug('get_room_anticipating')
        if room_id in self.energy_data[home_id]['rooms']:
            return( self.energy_data[home_id]['rooms'][room_id]['anticipating'])
        else:
            return(None)
        
    def get_room_heat_power_request(self, home_id, room_id):
        logging.debug('get_room_heat_power_request')
        if room_id in self.energy_data[home_id]['rooms']:
            return( self.energy_data[home_id]['rooms'][room_id]['heating_power_request'])
        else:
            return(None)


    def get_room_open_window(self, home_id, room_id):
        logging.debug('get_room_open_window')
        if room_id in self.energy_data[home_id]['rooms']:
            return( self.energy_data[home_id]['rooms'][room_id]['open_window'])
        else:
            return(None)


    def get_valve_online(self, home_id, valve_id):
        logging.debug('get_valve_online - data{} {} {}'.format(home_id, valve_id, self.energy_data) )
        if valve_id in self.energy_data[home_id]['modules']:
                return( self.energy_data[home_id]['modules'][valve_id]['reachable'])
        else:
            return(None)

    def get_valve_bat_state(self, home_id, valve_id):
        logging.debug('get_valve_bat_state')
        if valve_id in self.energy_data[home_id]['modules']:
            return( self.energy_data[home_id]['modules'][valve_id]['battery_state'])
        else:
            return(None)

    def get_valve_bat_level(self, home_id, valve_id):
        logging.debug('get_valve_bat_level')
        if valve_id in self.energy_data[home_id]['modules']:
            return( self.energy_data[home_id]['modules'][valve_id]['battery_level'])
        else:
            return(None)

    def get_valve_rf_strength(self, home_id, valve_id):
        logging.debug('get_valve_rf_strength')
        if valve_id in self.energy_data[home_id]['modules']:
            return( self.energy_data[home_id]['modules'][valve_id]['rf_strength'])
        else:
            return(None)


    def get_homectrl_homes(self):

        home_list = self.get_homes_info()
        logging.debug('get_homectrl_homes : {}'.format(home_list))
        self.ctrl_in_homes = {}
        for home_id, home in home_list.items():
            found = False
            home = home_list[home_id]
            logging.debug('get_homectrl_homes: {}'.format(home))
            if 'modules' in home:  
                for module in home['modules']:
                    logging.debug('Module : {}'.format(module))
                    if home['modules'][module]['type'] in self._dev_list:
                        found = True
                if found:
                    self.ctrl_in_homes[home_id] = home
        logging.debug('self.ctrl_in_homes {}'.format(self.ctrl_in_homes))
        return(self.ctrl_in_homes)

    def get_GW_modules(self, home_id):
        
        tmp = self._get_modules(home_id, self.GW_modules)
        logging.debug('get_GW_modules {}'.format(tmp))
        return(self._get_modules(home_id, self.GW_modules))
    



    def _get_energy_data(self, home_id, dev_id, mod_type):
 
        if home_id in self.energy_data:
            if mod_type in self.energy_data[home_id]:
                if dev_id in self.energy_data[home_id][mod_type]:
                    return(self.energy_data[home_id][mod_type][dev_id])
        else:
            logging.warning('No data fouond for {0} {1}'.format(home_id, dev_id))
    '''
    def get_main_module_data(self, home_id, dev_id):
        #Get data from main module
        logging.debug('get_main_module_data')
        #data_list = ['Temperature', 'CO2', 'Humidity', 'Noise', 'Pressure', 'AbsolutePressure', 'min_temp', 'max_temp', 'date_max_temp', 'date_min_temp', 'temp_trend', 'reachable']
        return(self._get_energy_data(home_id, dev_id, 'GW'))
    '''    

    def get_module_data(self, module):
        logging.debug('get_indoor_module_data')
        #data_list = ['temperature', 'co2', 'humidity', 'last_seen', 'battery_state', 'ts']
        return(self._get_energy_data(module['home_id'], module['module_id'], module['type']))
               
    '''
    def get_outdoor_module_data(self, home_id, dev_id=None):
        logging.debug('get_outdoor_module_data')
        #data_list = ['temperature', 'co2', 'humidity', 'last_seen', 'battery_state', 'ts']
        return(self._get_energy_data(home_id, dev_id, 'OUTDOOR'))

    def get_rain_module_data(self, home_id, dev_id=None):
        logging.debug('get_rain_module_data')
        #data_list = ['rain', 'sum_rain_1', 'sum_rail_24', 'last_seen', 'battery_state', 'ts']
        return(self._get_energy_data(home_id, dev_id, 'RAIN'))

    def get_wind_module_data(self, home_id, dev_id=None):
        logging.debug('get_wind_module_data')
        #data_list = ['wind_strength', 'wind_angle', 'wind+gust', 'wind_gust_angle', 'last_seen', 'battery_state', 'ts']
        return(self._get_energy_data(home_id, dev_id, 'WIND'))
    '''

    def get_temperature_C(self, module):
        try:
            logging.debug('get_temperature_C {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['temperature'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['temperature'])       
        except Exception as e:
            logging.error('get_temperature_C exception; {}'.format(e))
            return(None)
    def get_max_temperature_C (self, module):
        try:
            logging.debug('get_max_temperature_C {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['max_temp'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['max_temp'])       
        except Exception as e:
            logging.error('get_max_temperature_C exception; {}'.format(e))
            return(None)

    def get_min_temperature_C(self, module):
        try:
            logging.debug('get_min_temperature_C {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['min_temp'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['min_temp'])       
        except Exception as e:
            logging.error('get_min_temperature_C exception; {}'.format(e))
            return(None)

    def get_co2(self, module):
        try:
            logging.debug('get_co2 {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['co2'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['co2'])       
        except Exception as e:
            logging.error('get_co2 exception; {}'.format(e))
            return(None)

    def get_noise(self, module):
        try:
            logging.debug('get_noise {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['noise'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['noise'])       
        except Exception as e:
            logging.error('get_co2 exception; {}'.format(e))
            return(None)
        
    def get_humidity(self, module):
        try:
            logging.debug('get_humidity {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['humidity'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['humidity'])       
        except Exception as e:
            logging.error('get_humidity exception; {}'.format(e))
            return(None)

    def get_pressure(self, module):
        try:
            logging.debug('get_pressure {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['pressure'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['pressure'])       
        except Exception as e:
            logging.error('get_pressure exception; {}'.format(e))
            return(None)

    def get_abs_pressure(self, module):
        try:
            logging.debug('get_abs_pressure {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['absolute_pressure'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['absolute_pressure'])       
        except Exception as e:
            logging.error('absolute_pressure exception; {}'.format(e))
            return(None)        

    def get_time_stamp(self, module):
        try:
            logging.debug('get_time_stamp {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['time_stamp'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['time_stamp'])       
        except Exception as e:
            logging.error('get_time_stamp exception: {}'.format(e))
            return(None)        
             
    def get_time_since_time_stamp_min(self, module):
        unix_timestamp = datetime.now(timezone.utc).timestamp()
        meas_time = self.get_time_stamp(module)        
        delay = unix_timestamp - meas_time
        return( round(delay/60, 2)) #delay min

    def get_temp_trend(self, module):
        try:
            trend = self.energy_data[module['home_id']][module['type']][module['module_id']]['temp_trend']
            return(trend)       
        except Exception as e:
            logging.error('get_temp_trend exception; {}'.format(e))
            return( None)
    
    def get_hum_trend(self, module):
        try:
            trend = self.energy_data[module['home_id']][module['type']][module['module_id']]['pressure_trend']
   
        except Exception as e:
            logging.error('get_hum_trend exception; {}'.format(e))
            return( None, None)
        

    def get_rain(self, module):
        try:
            logging.debug('get_rain {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['rain'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['rain'])       
        except Exception as e:
            logging.error('get_rain exception; {}'.format(e))
            return(None)      

    def get_rain_1hour(self, module):
        try:
            logging.debug('get_rain_1hour {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['sum_rain_1'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['sum_rain_1'])       
        except Exception as e:
            logging.error('get_rain_1hour {}'.format(e))
            return(None)  
    
    def get_rain_24hours(self, module):
        try:
            logging.debug('get_rain_24hours {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['sum_rain_24'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['sum_rain_24'])       
        except Exception as e:
            logging.error('get_rain_24hours exception; {}'.format(e))
            return(None)  

    def get_wind_angle(self, module):
        try:
            logging.debug('get_wind_angle {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['windangle'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['windangle'])       
        except Exception as e:
            logging.error('get_wind_angle exception; {}'.format(e))
            return(None)  

    def get_wind_strength(self, module):
        try:
            logging.debug('get_wind_strength {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['windstrength'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['windstrength'])       
        except Exception as e:
            logging.error('get_wind_strength exception; {}'.format(e))
            return(None)  

    def get_gust_angle(self, module):
        try:
            logging.debug('get_wind_angle {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['gustangle'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['gustangle'])       
        except Exception as e:
            logging.error('get_wind_angle exception; {}'.format(e))
            return(None)  

    def get_gust_strength(self, module):
        try:
            logging.debug('get_wind_strength {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['guststrength'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['guststrength'])       
        except Exception as e:
            logging.error('get_wind_strength exception; {}'.format(e))
            return(None)  
        
    def get_max_wind_angle(self, module):
        try:
            logging.debug('get_wind_angle {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['max_wind_angle'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['max_wind_angle'])       
        except Exception as e:
            logging.error('get_wind_angle exception; {}'.format(e))
            return(None)  

    def get_max_wind_strength(self, module):
        try:
            logging.debug('get_wind_strength {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['max_wind_str'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['max_wind_str'])       
        except Exception as e:
            logging.error('get_wind_strength exception; {}'.format(e))
            return(None)          

    def get_battery_info(self, module):
        try:
            bat1 = self.energy_data[module['home_id']][module['type']][module['module_id']]['battery_state']
            bat2 = self.energy_data[module['home_id']][module['type']][module['module_id']]['battery_level']
            return (bat1, bat2)
        except Exception as e:
            logging.error('get_battery_info exception: {}'.format(e))
            return( None, None)
        
    def get_rf_info(self, module):
        try:
            rf1 = None
            rf2 = None
            if 'rf_state' in self.energy_data[module['home_id']][module['type']][module['module_id']]:
                rf1 = self.energy_data[module['home_id']][module['type']][module['module_id']]['rf_state']               
            if 'wifi_state' in self.energy_data[module['home_id']][module['type']][module['module_id']]:
                rf1 = self.energy_data[module['home_id']][module['type']][module['module_id']]['wifi_state']
            if 'rf_strength' in self.energy_data[module['home_id']][module['type']][module['module_id']]:
                rf2 = -self.energy_data[module['home_id']][module['type']][module['module_id']]['rf_strength']
            if 'wifi_strength' in self.energy_data[module['home_id']][module['type']][module['module_id']]:
                rf2 = -self.energy_data[module['home_id']][module['type']][module['module_id']]['wifi_strength']           
            return(rf1, rf2)
        except Exception as e:
            logging.error('get_rf_info exception; {}'.format(e))
            return(None, None)

    def get_online(self, module):
        try:
            #logging.debug('module {} '.format(module) )
            #logging.debug('module data1: {}'.format(self.energy_data))
            #logging.debug('module data2: {} - {} - {}'.format(module['home_id'], module['type'],module['module_id']))
            #logging.debug('module data3: {}'.format(self.energy_data[module['home_id']]))
            #logging.debug('module data4: {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]))
            #logging.debug('get_online {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['online'],module['home_id'], module['type'], module['module_id'] ))
            if 'online' in self.energy_data[module['home_id']][module['type']][module['module_id']]:    
                return(self.energy_data[module['home_id']][module['type']][module['module_id']]['online'])
            else:
                return(False)      
        except Exception as e:
            logging.warning('No online data exists - Assume off line : {} - {}'.format(e, module))
            return(False)


    '''