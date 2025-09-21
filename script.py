from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko import netmiko_send_command
from nornir.core.filter import F
import json

nr = InitNornir()

def show_arp():
    result = nr.run(
        task=netmiko_send_command,
        command_string="show arp",
        use_textfsm=True
    )
    print_result(result)

show_arp()
