import os
import meraki
import csv

dashboard = meraki.DashboardAPI()

# org_list = dashboard.organizations.getOrganizations()

# for org in org_list:
#     if org["name"] == "L-TWC Networks":
#         scs_org_id = org["id"]

# network_list = dashboard.organizations.getOrganizationNetworks(scs_org_id, total_pages='all')

# for network in network_list:
#     if network["name"] == "College Station":
#         my_network = network

with open('switch_list.csv') as file:
    csv_input_file = csv.reader(file)
    input_list = []
    headers = True
    for row in csv_input_file:
        if headers is True:
            headers = False
            continue
        input_list.append(row)

csv_cols = {
    'serial': 0,
    'hostname': 1,
    'ip address': 2,
    'subnet mask': 3,
    'gateway ip': 4,
    'dns1': 5,
    'dns2': 6,
    'mgmt vlan': 7,
    'port id': 8,
    'port name': 9,
    'enabled': 10,
    'poe enabled': 11,
    'type': 12,
    'vlan': 13,
    'allowed vlans': 14,
    'error': 15    
}

if len(input_list) > 10:
    batch = True
else:
    batch = False

org_id = "" # Will be populated with the Org ID once the org is confirmed

def setSwitchManagement(input_list, batch):
    failed_list = []
    failed_batch = []
    batch_list = []
    batch_list_key = 0
    row = 0
    if batch is False:
        print("*** Fewer than 10 updates loaded. Attempting configuration with individual API calls. ***\n")
        for switch in input_list:
            row += 1
            if switch[csv_cols['ip address']] == "" and switch[csv_cols['serial']] == "":
                continue
            elif switch[csv_cols['ip address']] == "" or switch[csv_cols['serial']] == "":
                print(f"!!! Skipping row {row}: Missing IP or Serial !!!\n")
                switch[csv_cols['error']] = "Missing IP or Serial"
                failed_list.append(switch)
                continue
            else:
                print("*** Setting management IP and VLAN for " + switch[csv_cols['serial']] + " ***\n")
                settings_dict = {
                    'wanEnabled': 'enabled',
                    'usingStaticIP': True,
                    'staticIp': switch[csv_cols['ip address']],
                    'staticSubnetMask': switch[csv_cols['subnet mask']],
                    'staticGatewayIP': switch[csv_cols['gateway ip']],
                    'staticDns': [switch[csv_cols['dns1']], switch[csv_cols['dns2']]],
                    'vlan': switch[csv_cols['mgmt vlan']]
                }
                try:
                    response = dashboard.devices.updateDeviceManagementInterface(
                        switch[csv_cols['serial']],
                        wan1=settings_dict
                    )
                    if response.status_code == 200:
                        print("*** Successfully configured " + switch[csv_cols['serial']] + " management ***\n\n")
                    else:
                        print("!!! Error occurred configuring " + switch[csv_cols['serial']] + " !!!\n\n")
                        switch[csv_cols['error']] = response.status_code
                        failed_list.append(switch)
                except:
                    print("An exception occurred\n\n")
                    
        if failed_list == []:
            print("*** All switch management configurations succeeded ***\n\n")
            return failed_list
        else:
            print("!!! One or more switches were not configured. Check the log file for more information. !!!\n\n")
            #errorLog(failed_list) errorLog function to be defined later
            return failed_list
    else:
        print("*** Ten or more updates detected. Loading configurations for batch update ***\n")
        for switch in input_list:
            row += 1
            if switch[csv_cols['ip address']] == "" and switch[csv_cols['serial']] == "":
                continue
            elif switch[csv_cols['ip address']] == "" or switch[csv_cols['serial']] == "":
                print("!!! Skipping row " + str(row) + ": Missing IP or Serial !!!\n")
                switch[csv_cols['error']] = "Missing IP or Serial"
                failed_list.append(switch)
                continue
            else:
                print("*** Adding management configs for " + switch[csv_cols['serial']] + " to batch ***\n")
                settings_dict = {
                    'resource': f"/devices/{switch[csv_cols['serial']]}/managementInterface",
                    'operation': 'update',
                    'body': {
                        'wanEnabled': 'enabled',
                        'usingStaticIP': True,
                        'staticIp': switch[csv_cols['ip address']],
                        'staticSubnetMask': switch[csv_cols['subnet mask']],
                        'staticGatewayIP': switch[csv_cols['gateway ip']],
                        'staticDns': [switch[csv_cols['dns1']], switch[csv_cols['dns2']]],
                        'vlan': switch[csv_cols['mgmt vlan']]
                    }
                }
                if len(batch_list[batch_list_key]) >= 100:
                    batch_list_key += 1
                batch_list[batch_list_key].append(settings_dict)
        key = 0
        total = len(batch_list)
        for list in batch_list:
            key += 1
            print(f"*** Attempting batch {key} out of {total} ***\n")
            try:
                response = dashboard.organizations.createOrganizationActionBatch(
                    org_id, actions=list,
                    confirmed=True,                
                )
                if response['status']['errors'] == "":
                    print("*** Successfully completed batch configuration ***\n\n")
                else:
                    print(f"!!! Error occurred during batch {key} !!!\n\n")
                    failed_list.append([list, response['status']['errors']])
                
            except:
                print("An exception occurred\n\n")
                
        if failed_list == []:
            print("*** All switch management configurations succeeded ***\n\n")
        else:
            print("!!! One or more switches were not configured. Check the log file for more information. !!!\n\n")
            #errorLog(failed_list) errorLog function to be defined later

def setSwtichPorts(input_list, batch):
    failed_list = []
    batch_list = []
    batch_list_key = 0
    row = 0
    if batch is False:
        for switch in input_list:
            row += 1
            if switch[csv_cols['serial']] == "" and switch[csv_cols['port id']] == "":
                continue
            elif switch[csv_cols['serial']] == "" or switch[csv_cols['port id']] == "":
                print("!!! Skipping row " + str(row) + ": Missing Serial or Port ID !!!\n")
                switch[csv_cols['error']] = "Missing Serial or Port ID"
                failed_list.append(switch)
                continue
            else:
                print(f"*** Configuring port {switch[csv_cols['port id']]} for {switch[csv_cols['serial']]} ***\n")
                try:
                    response = dashboard.switch.updateDeviceSwitchPort(
                        switch[csv_cols['serial']], switch[csv_cols['port id']],
                        name=switch[csv_cols['hostname']],
                        enabled=switch[csv_cols['enabled']],
                        poeEnabled=switch[csv_cols['poe enabled']],
                        type=switch[csv_cols['type']],
                        vlan=switch[csv_cols['vlan']],
                        allowedVlans=switch[csv_cols['allowed vlans']]
                    )
                    if response.status_code == 200:
                        print(f"*** Successfully configured port {switch[csv_cols['port id']]} for {switch[csv_cols['serial']]} ***\n\n")
                    else:
                        print(f"!!! Error occurred configuring port {switch[csv_cols['port id']]} for {switch[csv_cols['serial']]} !!!\n\n")
                        switch[csv_cols['error']] = response.status_code
                        failed_list.append(switch)
                except:
                    print("An exception occurred\n\n")
                    
        if failed_list == []:
            print("*** All switch management configurations succeeded ***\n\n")
            return failed_list
        else:
            print("!!! One or more switches were not configured. Check the log file for more information. !!!\n\n")
            #errorLog(failed_list) errorLog function to be defined later
            return failed_list
    else:
        print("*** Ten or more updates detected. Loading configurations for batch update ***\n")
        for switch in input_list:
            row += 1
            if switch[csv_cols['serial']] == "" and switch[csv_cols['port id']] == "":
                continue
            elif switch[csv_cols['serial']] == "" or switch[csv_cols['port id']] == "":
                print(f"!!! Skipping row {row}: Missing IP or Serial !!!\n")
                switch[csv_cols['error']] = "Missing IP or Port"
                failed_list.append(switch)
                continue
            else:
                print("*** Adding management configs for " + switch[csv_cols['serial']] + " to batch ***\n")
                settings_dict = {
                    'resource': f"/devices/{switch[csv_cols['serial']]}/switch/ports/{switch[csv_cols['port id']]}",
                    'operation': 'update',
                    'body': {
                        'name': switch[csv_cols['hostname']],
                        'enabled': switch[csv_cols['enabled']],
                        'poeEnabled': switch[csv_cols['poe enabled']],
                        'type': switch[csv_cols['type']],
                        'vlan': switch[csv_cols['vlan']],
                        'allowedVlans': switch[csv_cols['allowed vlans']]
                    }
                }
                if len(batch_list[batch_list_key]) >= 100:
                    batch_list_key += 1
                batch_list[batch_list_key].append(settings_dict)
        key = 0
        total = len(batch_list)
        for list in batch_list:
            key += 1
            print(f"*** Attempting batch {key} out of {total} ***\n")
            try:
                response = dashboard.organizations.createOrganizationActionBatch(
                    org_id, actions=list,
                    confirmed=True,                
                )
                if response['status']['errors'] == "":
                    print("*** Successfully completed batch configuration ***\n\n")
                else:
                    print(f"!!! Error occurred during batch {key} !!!\n\n")
                    failed_list.append([list, response['status']['errors']])
                
            except:
                print("An exception occurred\n\n")
                
        if failed_list == []:
            print("*** All switch management configurations succeeded ***\n\n")
        else:
            print("!!! One or more switches were not configured. Check the log file for more information. !!!\n\n")
            #errorLog(failed_list) errorLog function to be defined later