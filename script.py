from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko import netmiko_send_command
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_get
import json
from napalm import get_network_driver
import os
from mac_vendor_lookup import MacLookup

nr = InitNornir()

def show_arp_aruba():
    filtered_hosts = nr.filter(F(groups__contains="aruba"))
    result = filtered_hosts.run(
        task=netmiko_send_command,
        command_string="show arp all-vrfs",
        use_textfsm=True,
        textfsm_template="/home/admin/python/nornir/mac_address_export/templates/aruba_aoscx_show_arp_all-vrfs.textfsm"
    )
#     print_result(result)
    #Loop through the results and write to CSV files.
    for host_name, multi_result in result.items():  # Loop through each host's results
        with open(f"{host_name}.csv", "w") as f:  # Create a CSV file for each host
            f.write("device_name,vrf,ip_address,mac_address,vendor,interface\n")  # Write CSV header
            for host_name, multi_result in result.items():  # Loop again over each host
                output_list = (multi_result[0].result)
                for entry in output_list:
                    ip_address = entry['ip_address']
                    mac_address = entry['mac_address']
                    interface = entry['physical_port']
                    vrf = entry['vrf']
                    try:
                        vendor = MacLookup().lookup(mac_address)
                        print(f"Generating vendor info ({vendor})")
                    except:
                        vendor = "N/A"
                        print("No vendor info found")

                    f.write(f"{host_name},{vrf},{ip_address},{mac_address},{vendor},{interface}\n")
        print(f"ARP output saved to {host_name}.csv")
def show_arp_ios():
    driver = get_network_driver("ios")
    filtered_hosts = nr.filter(F(groups__contains="cisco"))
    result = filtered_hosts.run(task=napalm_get,
                                getters=["get_arp_table"])

    # print_result(result)
    for host_name, multi_result in result.items():  # Loop through each host
        output_dict = (multi_result[0].result)

        with open(f"{host_name}.csv", "a") as f:  # Append mode
            # Write a CSV header
            f.write("device_name,vrf,ip_address,mac_address,vendor,interface\n")

            for entry in output_dict['get_arp_table']:
                ip_address = entry['ip']
                mac_address = entry['mac']
                interface = entry['interface']
                try:
                    vendor = MacLookup().lookup(mac_address)
                    print(f"Generating vendor info ({vendor})")
                except:
                    vendor = "N/A"
                    print("No vendor info found")
                f.write(f"{host_name},default,{ip_address},{mac_address},{vendor},{interface}\n")
        print(f"ARP output saved to {host_name}.csv")

show_arp_aruba()