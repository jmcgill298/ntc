import pyeapi
import requests
from getpass import getpass
from netmiko import ConnectHandler


class NxSwitch:
    """
    This class is used to interact with NX-API using the requests module.
    These requests use json-rpc for the output, and creating this initializes
    the device, username, password, and other basic request formatting.
    """

    def __init__(self, host, user, pw=None, jsonrpc='2.0', method='cli',
                 ver=1, cont_type={'content-type': 'application/json-rpc'}):
        """
        This initializes the Nexus Switch object.

        :param host: The device which is being worked on
        :param user: The username to login to the device
        :param pw: The password used for the user account, defaults to
        use getpass to retrieve the password more securely.
        :param jsonrpc: The version used by NX-API
        :param method: The method for the NX-API called
        :param ver: Required argument for NX-API call
        :param cont_type: The header to pass in the HTTP request to
        identify the type of data being passed.
        """
        self.host = host
        self.user = user
        if pw == None:
            self.pw = getpass('What is your password: ')
        else:
            self.pw = pw
        self.jsonrpc = jsonrpc
        self.method = method
        self.ver = ver
        self.cont_type = cont_type

    def nx_cdp(self):
        """
        This function is used to view cdp neighbors of the switch.

        :return: Returns the results from a HTTP POST request
        to retrieve the output of 'show cdp neighbors.'
        """
        requests.packages.urllib3.disable_warnings()
        url = 'https://{}:8443/ins'.format(self.host)
        payload = [
            {
                "jsonrpc": self.jsonrpc,
                "method": self.method,
                "params": {
                    "cmd": "show cdp neighbor",
                    "version": self.ver,
                },
                "id": 1
            }
        ]

        return requests.post(url, json=payload, headers=self.cont_type,
                             auth=(self.user, self.pw), verify=False)


class IosSwitch:
    """
    This class is used to interact with IOS switches using the Netmiko module.
    """

    def __init__(self, host, user, pw=None):
        """
        This initializes the IOS object.

        :param host: The device which is being worked on
        :param user: The username to login to the device
        :param pw: The password used for the user account, defaults to
        use getpass to retrieve the password more securely.
        """
        self.host = host
        self.user = user
        if pw == None:
            self.pw = getpass('What is your password: ')
        else:
            self.pw = pw

    def ios_cdp(self):
        """
        This function is used to view the cdp neighbors of the switch.

        :return: Returns the results of a 'show cdp neighbors' command.
        """
        connection = ConnectHandler(device_type='cisco_ios', ip=self.host,
                                    username=self.user, password=self.pw)
        connection.send_command("terminal length 0")
        return connection.send_command('show cdp neighbor')


class EosSwitch:
    """
    This class is used to interact with Arista switches using
    their pyeapi library. This library uses a host ini file
    to collect hostnames, usernames, and passwords.
    """

    def __init__(self, host):
        """
        This initializes the Arista switch
        """
        self.host = host

    def eos_connect(self):
        """
        This function creates a connection to the Arista switch.
        This will be used for other requests for AAA functions.

        :return: Returns an open connection to the switch.
        """
        return pyeapi.connect_to(self.host)

    def eos_lldp_neighbors(self, switch_conn):
        """
        This function is used collect lldp neighbor information
        from the switch.

        :param switch_conn: An open connection to the switch.
        :return: The lldp neighbors of the switch.
        """
        return switch_conn.enable('show lldp neighbors')
