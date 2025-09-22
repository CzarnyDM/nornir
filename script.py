from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko import netmiko_send_command
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_get
import json
from napalm import get_network_driver
from mac_vendor_lookup import MacLookup


nr = InitNornir()

driver = get_network_driver("ios")
driver = get_network_driver("junos")


def show_arp_napalm():
        result = nr.run(task=napalm_get, 
                        getters=["get_arp_table"], )
        print_result(result)


def show_arp():
        arp_json = []
        filtered_hosts = nr.filter(F(groups__contains="aruba"))
        result = filtered_hosts.run(
        task=netmiko_send_command,
        command_string="show arp",
    )
        print_result(result)
        for host, task_result in result.items():
                # task_result is a MultiResult object; first element has .result
                output = task_result[0].result
                for line in output.splitlines()[2:-2]:  # skip header and footer
                        parts = line.split()
                        if len(parts) >= 4:  # make sure line has all columns
                                arp_json.append({
                                "ip": parts[0],
                                "mac": parts[1],
                                "port": parts[2]
                                })
        arp_json = json.dumps(arp_json, indent=4)
        print(arp_json)

# def vendor_lookup():
#         mac = MacLookup()
#         vendor = mac.lookup(arp_json['mac'])
#         print(vendor)


arp_json = show_arp()
type(arp_json)