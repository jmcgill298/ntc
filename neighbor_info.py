import re
import json
import datetime
from pprint import pprint
from csv import DictReader
from getpass import getpass
from switch_classes import NxSwitch, IosSwitch, EosSwitch


def main():
    """
    This function loads an inventory CSV and uses the  appropriate
    function to parse the data into a dictionary with keys:
    'neighbor_interface', 'local_interface', and 'neighbor.' Each 
    device in the inventory file will have a list with these
    dictionaries.

    :return: This will pretty print the neighbors, and also save
    a file named 'neighbors_(date).json' for historical data.
    """
    user = input('What is your username: ')
    pw = getpass('What is your password: ')
    inventory = DictReader(open('inventory.csv'))
    inv_dict = {}

    for device in inventory:
        if device['os'] == 'nxos':
            inv_dict[device['hostname']] = nxos_cdp_filter(device['ip'], user, pw)

        elif device['os'] == 'ios':
            inv_dict[device['hostname']] = ios_cdp_filter(device['ip'], user, pw)

        elif device['os'] == 'eos':
            inv_dict[device['hostname']] = eos_lldp_filter(device['hostname'])

    pprint(inv_dict)

    datestamp = datetime.date.today()
    fout = open('neighbors_{}.json'.format(datestamp), 'w')
    fout.write(json.dumps(inv_dict))
    fout.close()


def nxos_cdp_filter(device, user, pw=None):
    """
    This function is used to retrieve and filter cdp
    data on Nexus switches using the NxSwitch class.

    :param device: The switch to retrieve cdp neighbors from.
    :param user: The user account to login to the switch.
    :param pw: The password for the user account; if blank
    getpass will be used to retrieve it more securely.

    :return: A list of dictionaries with the filtered cdp neighbor
    information. The keys are: 'neighbor_interface', 'local_interface',
    and 'neighbor.'
    """
    nxos_switch = NxSwitch(device, user, pw)
    cdp_request = nxos_switch.nx_cdp()
    if cdp_request.ok:
        cdp_data = nxos_switch.nx_cdp().json()
        cdp_filtered = cdp_data['result']['body']['TABLE_cdp_neighbor_brief_info']['ROW_cdp_neighbor_brief_info']

        all_neighbors = []
        for neighbor in cdp_filtered:
            neighbor_dict = {
                "neighbor_interface": neighbor['port_id'],
                "local_interface": neighbor['intf_id'],
                "neighbor": neighbor['device_id']
            }

            all_neighbors.append(neighbor_dict)

        return all_neighbors

    else:
        print('The request failed! status_code: {}\nreason: {}\ncontent: {}'.format(
            cdp_request.status_code, cdp_request.reason, cdp_request.content
        ))


def ios_cdp_filter(device, user, pw=None):
    """
    This function is used to retrieve and filter cdp
    data on IOS devices using the IosSwitch class.
    The regex works whether the cdp neighbor takes one
    or more lines, and accounts for varying capabilities.

    :param device: The switch to retrieve cdp neighbors from.
    :param user: The user account to login to the switch.
    :param pw: The password for the user account; if blank
    getpass will be used to retrieve it more securely.

    :return: A list of dictionaries with the filtered cdp neighbor
    information. The keys are: 'neighbor_interface', 'local_interface',
    and 'neighbor.'
    """
    try:
        ios_switch = IosSwitch(device, user, pw)
        cdp_data = ios_switch.ios_cdp()

        rel_cdp_info = cdp_data.split('Port ID\n')[1]
        regex = '(\S+)\s+(\S+ \S+)\s+(\S+)\s+((\S \S \S \S \S)|(\S \S \S \S)|(\S \S \S)|(\S \S)|(\S))\s+(\S+)\s+(.*)'
        cdp_neighbors = re.findall(regex, rel_cdp_info)

        all_neighbors = []
        for neighbor in cdp_neighbors:
            neighbor_dict = {
                "neighbor_interface": neighbor[10],
                "local_interface": neighbor[1],
                "neighbor": neighbor[0]
            }

            all_neighbors.append(neighbor_dict)

        return all_neighbors

    except:
        print("Couldn't login into {}".format(device))


def eos_lldp_filter(device):
    """
    This function is used to retrieve and filter lldp
    data on Arista switches using the EosSwitch class.

    :param device: The connection value for the switch in the
    configuratoin file for pyeapi.

    :return: A list of dictionaries with the filtered cdp neighbor
    information. The keys are: 'neighbor_interface', 'local_interface',
    and 'neighbor.'
    """
    eos_switch = EosSwitch(device)
    try:
        eos_switch_conn = eos_switch.eos_connect()
        lldp_data = eos_switch.eos_lldp_neighbors(eos_switch_conn)[0]

        all_neighbors = []
        for neighbor in lldp_data['result']['lldpNeighbors']:
            neighbor_dict = {
                "neighbor_interface": neighbor['neighborPort'],
                "local_interface": neighbor['port'],
                "neighbor": neighbor['neighborDevice']
            }

            all_neighbors.append(neighbor_dict)

        return all_neighbors

    except:
        print("Couldn't login into: {}".format(device))


if __name__ == '__main__':
    main()
