from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko import netmiko_send_command
from nornir.core.filter import F
import json

nr = InitNornir()

def show_arp():
    cisco_nr = nr.filter(F(platform="aruba_aoscx"))
    result = cisco_nr.run(
        task=netmiko_send_command,
        command_string="show arp",
        use_textfsm=True
    )

show_arp()
