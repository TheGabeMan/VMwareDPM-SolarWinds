#!/usr/bin/python3
import json
import os
import datetime
import logging
import requests
from datetime import timezone

def main():
    ''' Script to mute and unmute SolarWinds managed nodes '''

    server = '1.1.1.1' 
    sw_rest_url = "https://1.1.1.1:17778/SolarWinds/InformationService/v3/Json"
    username = 'user@domain.com' # Service account with API permissions in solarwinds
    password = 'password'
    logging.basicConfig(filename='/var/scripts/connect_solarwinds.log', level=logging.INFO)

    write_log_info('SolarWinds Script start')

    alarm_name = os.getenv('VMWARE_ALARM_NAME', 'leeg')
    alarm_target_name = os.getenv('VMWARE_ALARM_TARGET_NAME', 'debug_VMWARE_ALARM_TARGET_NAME')
    event_decscription = os.getenv('VMWARE_ALARM_EVENTDESCRIPTION', 'debug_VMWARE_ALARM_EVENTDESCRIPTION')

    write_log_info(alarm_name)              # Host is IN standby mode - DPM  / Host is UIT standby mode - DPM 
    write_log_info(alarm_target_name)
    write_log_info(event_decscription)      # DRS put host into standby mode / DRS moved host out of standby mode

    ## search Node from alarm_target_name
    write_log_info( 'Search node ' + alarm_target_name )
    uri = get_sw_node_by_name(sw_rest_url, alarm_target_name)
    write_log_info( 'Search result: ' + uri )

    ## Current SolarWinds status for this node:
    current_state = Get_SuppressionState(sw_rest_url, uri)
    if current_state['SuppressionMode'] == 1:
        write_log_info('Node '+ alarm_target_name + ' alerts are currently muted.')
    else:
        write_log_info('Node '+ alarm_target_name + ' is active.')

    if event_decscription.find('DRS put') != -1 and event_decscription.find('into standby mode') != -1:
        ''' DRS put host into standby mode '''
        SuppressAlerts(sw_rest_url, uri)
        write_log_info('Node '+ alarm_target_name + ' muted.')

    if event_decscription.find('DRS moved') != -1 and event_decscription.find('out of standby mode') != -1:
        ''' DRS moved host out of standby mode '''
        ResumeAlerts(sw_rest_url, uri)
        write_log_info('Node '+ alarm_target_name + ' alerts resumed.')

    if event_decscription.find('DRS cannot move') != -1 and event_decscription.find('out of standby mode') != -1:
        ''' Alarm host failed to startup out of standby mode on Host '''
        ''' When host doesn't wake from standby as expected, we do enable the monitoring '''
        ''' to trigger a solarwinds alert. '''
        ResumeAlerts(sw_rest_url, uri)
        write_log_info('Node '+ alarm_target_name + ' alerts resumed.')
    
    ## Current SolarWinds status for this node:
    current_state = Get_SuppressionState(sw_rest_url, uri)
    if current_state['SuppressionMode'] == 1:
        write_log_info('Node '+ alarm_target_name + ' alerts are muted.')
    else:
        write_log_info('Node '+ alarm_target_name + ' is active.')

    # Script has finished
    write_log_info('SolarWinds Script finished')


def write_log_info(text):
    logging.info(datetime.datetime.now().strftime("%m/%d/%Y-%H:%M:%S") + " --- " + text)


def Get_SuppressionState(sw_rest_url, uri):
    ''' Get Alert Suppression State '''
    url = sw_rest_url + "/Invoke/Orion.AlertSuppression/GetAlertSuppressionState"
    payload = json.dumps({"entityUris": [f"{uri}"]})
    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic <base64 code>'
    }
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    
    return response.json()[0]


def SuppressAlerts(sw_rest_url, uri):
    ''' Suppress Alerts for this node '''
    now = datetime.datetime.now()
    nowutc = now.astimezone(timezone.utc)
    print('UTC: ', nowutc)

    url = sw_rest_url + "/Invoke/Orion.AlertSuppression/SuppressAlerts"
    payload = json.dumps({"entityUris": [f"{uri}"], "suppressFrom": f"{nowutc}"})

    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic <base64 code>'
    }
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    print('Mute Alerts')


def ResumeAlerts(sw_rest_url, uri):
    ''' ResumeAlerts '''
    url = sw_rest_url + "/Invoke/Orion.AlertSuppression/ResumeAlerts"
    payload = json.dumps({"entityUris": [f"{uri}"]})

    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic <base64 code>'
    }
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    print('Resume Alerting')



def get_sw_node_by_ip(sw_rest_url, ip_address):
    ''' find sw node '''
    url = sw_rest_url + "/query?query=SELECT Uri FROM Orion.Nodes WHERE IPAddress='" + ip_address + "'"
    payload={}
    headers = {
    'Authorization': 'Basic <base64 code>'
    }
    response = requests.request("GET", url, headers=headers, data=payload, verify=False)
    return response.json()['results'][0]['Uri']


def get_sw_node_by_name(sw_rest_url, node_name):
    ''' find sw node '''
    url = sw_rest_url + "/query?query=SELECT Uri FROM Orion.Nodes WHERE NODENAME='" + node_name + "'"
    payload={}
    headers = {
    'Authorization': 'Basic <base64 code>'
    }
    response = requests.request("GET", url, headers=headers, data=payload, verify=False)
    return response.json()['results'][0]['Uri']
    

if __name__ == "__main__":
    main()
