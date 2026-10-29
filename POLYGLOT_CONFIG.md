## Netatmo  NodeServer Configuration
####Configuration Parameters:

- key: shortPoll, value: Time between refresh of critical data in sec. 
- key: longPoll, value: Time between refresh of all data in sec.

####Custom Configuration Parameters:

- key: ClientID, value: cliendID from Netatmo developer User App 
- key: ClientSecret, value: cliendSecret from Netatmo developer User App 
- key: TEMP_UNIT, value: Temperature reporting unit (F or C)
- key: WEBHOOK_URL, value: (Optional) HTTPS callback URL for real-time switch/remote push events (e.g. from ISY Portal: https://my.isy.io/api/eisy/pg3/webhook/noresponse/<uuid>/<slot>)
- key: XXXX, value : Enable (1) or disable (0) XXXX Home with energy system