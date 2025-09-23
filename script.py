# main.py
from nornir import InitNornir
import os
from datetime import datetime
import time
import inquirer
import logging

# Import helper functions
from functions import show_arp_ios_to_excel, show_arp_aruba_to_excel, obtain_vrfs_to_excel

# Init Nornir
nr = InitNornir(config_file="inventory/config.yaml")

# Paths
date = datetime.now().strftime("%Y-%m-%d")
date_and_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
output_dir = "./output"
os.makedirs(output_dir, exist_ok=True)

# Logging
logging.basicConfig(
    filename=f"./logs/log_{date_and_time}.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Execution time tracker
start_time = time.perf_counter()
end_time = time.perf_counter()
execution_time = end_time - start_time

print("Please wait...")
# User prompt
def user_prompt():
    logging.info("Script started")
    user_prompt = [
        inquirer.List('device', message="Select the ship", choices=['Cisco IOS', 'Aruba AOS-CX', 'Both'])
    ]
    answers = inquirer.prompt(user_prompt)

    if answers['device'] == 'Cisco IOS':
        show_arp_ios(nr, output_dir, date, execution_time)
        obtain_vrfs(nr, output_dir, date, execution_time)
    elif answers['device'] == 'Aruba AOS-CX':
        show_arp_aruba(nr, output_dir, date, execution_time)
    elif answers['device'] == 'Both':
        show_arp_ios(nr, output_dir, date, execution_time)
        obtain_vrfs(nr, output_dir, date, execution_time)
        show_arp_aruba(nr, output_dir, date, execution_time)

# Run
if __name__ == "__main__":
    user_prompt()
