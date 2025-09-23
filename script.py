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
import time
from getpass import getpass
from pprint import pprint
import csv
import inquirer
import logging

nr = InitNornir(config_file="inventory/config.yaml")
date = datetime.now().strftime("%Y-%m-%d")
date_and_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
output_dir = "./output"
output = "./output/"
os.makedirs(output_dir, exist_ok=True)

logging.basicConfig(
    filename=f"./logs/log_{date_and_time}.txt",             # Log file path
    level=logging.INFO,             # Minimum level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    datefmt="%Y-%m-%d %H:%M:%S"
)
# -----------------EXECUTION TIME---------------------

start_time = time.perf_counter()

for i in range(1000000):
    pass

end_time = time.perf_counter()
execution_time = end_time - start_time

# ---------------------------------------------------------
# ---------------BIND TIMESTAMP TO THE PRINT---------------

def tprint(*args, **kwargs):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}]", *args, **kwargs)

# ---------------------------------------------------------


# --------------------FUNCITONS-----------------------------
# ---------------------------------------------------------
def show_arp_aruba():
    start_time
    filtered_hosts = nr.filter(F(groups__contains="aruba"))
    result = filtered_hosts.run(
        task=netmiko_send_command,
        command_string="show arp all-vrfs",
        use_textfsm=True,
        textfsm_template="/home/admin/python/nornir/mac_address_export/templates/aruba_aoscx_show_arp_all-vrfs.textfsm"
    )
    # print_result(result)

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
                    logging.info(f"Generating vendor info ({vendor})")
                except:
                    vendor = "N/A"
                    logging.info(f"No vendor info found for {mac_address}")

                f.write(f"{host_name},{vrf},{ip_address},{mac_address},{vendor},{interface}\n")

        tprint(f"Output saved to {host_name}_{date}.csv")
        end_time
        logging.info(f"Script executed for {host_name} in {execution_time} seconds")


# ---------------------------------------------------------
def show_arp_ios():
    start_time
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
                    logging.info(f"Generating vendor info ({vendor})")
                except Exception:
                    vendor = "N/A"
                    logging.info(f"No vendor info found for {mac_address}")
                f.write(f"{host_name},default,{ip_address},{mac_address},{vendor},{interface}\n")

        tprint(f"Output saved to {host_name}_{date}.csv")
        end_time
        logging.info(f"Script executed for {host_name} in {execution_time} seconds")

# ---------------------------------------------------------
def obtain_vrfs():
    start_time
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
            logging.info(f"Quering the ARP table for the VRF - {vrf_name} on {host_name}")

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
                        logging.info(f"Generating vendor info ({vendor})")
                    except Exception:
                        vendor = "N/A"
                        logging.info(f"No vendor info found for {mac_address}")
                    f.write(f"{host_name},{vrf_name},{ip_address},{mac_address},{vendor},{interface}\n")

            logging.info(f"Output appended to {host_name}_{date}.csv")
            end_time
            logging.info(f"Script executed for {host_name} in {execution_time} seconds")

# ---------------------------------------------------------

def user_prompt():
    print("PLEASE WAIT")
    logging.info("Script started")
    user_prompt = [
        inquirer.List('device', message="Select the ship", choices=['Cisco IOS', 'Aruba AOS-CX', 'Both'])
    ]
    answers = inquirer.prompt(user_prompt)

    if answers['device'] == 'Cisco IOS':
        show_arp_ios()
        obtain_vrfs()
    elif answers['device'] == 'Aruba AOS-CX':
        show_arp_aruba()
    elif answers['device'] == 'Both':
        show_arp_ios()
        obtain_vrfs()
        show_arp_aruba()

# ---------------------------------------------------------
# --------------------MAIN PROGRAM--------------------------
# ---------------------------------------------------------

user_prompt()