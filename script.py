from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko import netmiko_send_command
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_get
import json
from napalm import get_network_driver


nr = InitNornir()

driver = get_network_driver("ios")
driver = get_network_driver("junos")


def show_arp_napalm():
        result = nr.run(task=napalm_get, 
                        getters=["get_arp_table"], )
        # print_result(result)
        
        mac_address = []
        

def show_arp():
        result = nr.run(
        task=netmiko_send_command,
        command_string="show arp",
        use_textfsm=True
    )


show_arp_napalm()