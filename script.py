from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko import netmiko_send_command
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_get
import json
from napalm import get_network_driver
import os
from mac_vendor_lookup import MacLookup
from datetime import datetime
from getpass import getpass
from pprint import pprint
import csv

date = datetime.now().strftime("%Y-%m-%d")

output_dir = "./output"
os.makedirs(output_dir, exist_ok=True)


def tprint(*args, **kwargs):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}]", *args, **kwargs)


output = "./output/"

nr = InitNornir(config_file="inventory/config.yaml")

# ---------------------------------------------------------
def show_arp_aruba():
    filtered_hosts = nr.filter(F(hostname="172.28.4.67"))
    result = filtered_hosts.run(
        task=netmiko_send_command,
        command_string="show arp all-vrfs",
        use_textfsm=True,
        textfsm_template="/home/docker/scripts/device_scanner/template/aruba_aoscx_show_arp_all-vrfs.textfsm"
    )
    print_result(result)

    # Loop through the results and write to CSV files
    for host_name, multi_result in result.items():  # Loop through each host's results
        if multi_result.failed:
            tprint(f"⚠️ Skipping {host_name} (command failed or host unreachable)")
            continue

        output_file = os.path.join(output, f"{host_name}_{date}.csv")
        with open(output_file, "w") as f:  # Create a CSV file for each host
            f.write("device_name,vrf,ip_address,mac_address,vendor,interface\n")  # Write CSV header

            output_list = multi_result[0].result
            for entry in output_list:
                ip_address = entry['ip_address']
                mac_address = entry['mac_address']
                interface = entry['physical_port']
                vrf = entry['vrf']

                try:
                    vendor = MacLookup().lookup(mac_address)
                    tprint(f"Generating vendor info ({vendor})")
                except:
                    vendor = "N/A"
                    tprint("No vendor info found")

                f.write(f"{host_name},{vrf},{ip_address},{mac_address},{vendor},{interface}\n")

        tprint(f"ARP output saved to {output_file}")


# ---------------------------------------------------------
def show_arp_ios():
    filtered_hosts = nr.filter(F(groups__contains="cisco"))
    result = filtered_hosts.run(
        task=napalm_get,
        getters=["get_arp_table"]
    )

    for host_name, multi_result in result.items():  # Loop through each host
        if multi_result.failed:
            tprint(f"⚠️ Skipping {host_name} (command failed or host unreachable)")
            continue

        output_dict = multi_result[0].result
        output_file = os.path.join(output_dir, f"{host_name}_{date}.csv")
        file_exists = os.path.isfile(output_file)

        with open(output_file, "a") as f:
            if not file_exists:
                f.write("device_name,vrf,ip_address,mac_address,vendor,interface\n")

            for entry in output_dict.get('get_arp_table', []):
                ip_address = entry.get("ip", "")
                mac_address = entry.get("mac", "")
                interface = entry.get("interface", "")

                try:
                    vendor = MacLookup().lookup(mac_address)
                except Exception:
                    vendor = "N/A"

                f.write(f"{host_name},default,{ip_address},{mac_address},{vendor},{interface}\n")

        tprint(f"ARP output saved to {output_file}")


# ---------------------------------------------------------
def obtain_vrfs():
    date = datetime.now().strftime("%Y-%m-%d")
    output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)

    filtered_hosts = nr.filter(F(groups__contains="cisco"))
    vrf_results = filtered_hosts.run(
        task=netmiko_send_command,
        command_string="show vrf",
        use_textfsm=True,
        textfsm_template="/home/admin/python/nornir/mac_address_export/templates/cisco_ios_show_vrf.textfsm"
    )

    for host_name, multi_result in vrf_results.items():
        if multi_result.failed:
            tprint(f"⚠️ Skipping {host_name} (command failed or host unreachable)")
            continue

        vrfs = multi_result[0].result

        for entry in vrfs:
            vrf_name = entry["name"]
            tprint(f"Running show arp vrf {vrf_name} on {host_name}")

            arp_result = filtered_hosts.run(
                task=netmiko_send_command,
                command_string=f"show arp vrf {vrf_name}",
                use_textfsm=True,
                textfsm_template="/home/admin/python/nornir/mac_address_export/templates/cisco_ios_show_arp.textfsm"
            )

            output_file = os.path.join(output_dir, f"{host_name}_{date}.csv")
            file_exists = os.path.isfile(output_file)

            with open(output_file, "a") as f:
                if not file_exists:
                    f.write("device_name,vrf,ip_address,mac_address,vendor,interface\n")

                output_dict = arp_result[host_name][0].result
                for row in output_dict:
                    ip_address = row.get("address", "")
                    mac_address = row.get("hardware_address", "")
                    interface = row.get("interface", "")

                    try:
                        vendor = MacLookup().lookup(mac_address)
                    except Exception:
                        vendor = "N/A"

                    f.write(f"{host_name},{vrf_name},{ip_address},{mac_address},{vendor},{interface}\n")

            tprint(f"ARP output appended to {output_file}")


# Call the function
obtain_vrfs()
show_arp_ios()