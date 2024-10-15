import psutil
import platform
from datetime import datetime
import cpuinfo
import socket
import uuid
import re
import getpass
import json
import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys
import time
import traceback
import tkinter as tk
from tkinter import messagebox

def get_creds_path():
    if getattr(sys, 'frozen', False):  # Check if the program is frozen
        creds_path = os.path.join(sys._MEIPASS, 'creds.json')  # Get the path to the temporary directory
        print(f"Using frozen creds path: {creds_path}")
        return creds_path
    else:
        print("Using normal creds path: creds.json")
        return 'creds.json'  # Normal execution

# Initialize Firebase with Firestore
try:
    cred = credentials.Certificate(get_creds_path())
    firebase_admin.initialize_app(cred)
    print("Firebase initialized successfully.")
except Exception as e:
    print(f"Failed to initialize Firebase: {e}")
    sys.exit(1)

def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            size = f"{bytes:.2f}{unit}{suffix}"
            print(f"Formatted size: {size}")
            return size
        bytes /= factor

def System_information():
    try:
        print("Gathering system information...")
        uname = platform.uname()
        print(uname)

        user = getpass.getuser()
        print(f"User: {user}")

        pc_name = uname.node
        print(f"PC Name: {pc_name}")

        os_info = f"{uname.system} {uname.release} ({uname.version})"
        print(f"OS Info: {os_info}")

        processor = uname.processor
        print(f"Processor: {processor}")

        ram = get_size(psutil.virtual_memory().total)
        print(f"RAM: {ram}")

        ip_address = get_ip_address()
        print(f"IP Address: {ip_address}")

        mac_address = get_mac_address()
        print(f"MAC Address: {mac_address}")

        boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime('%Y/%m/%d %H:%M:%S')
        print(f"Boot Time: {boot_time}")

        partitions = get_partitions()
        print(f"Partitions: {partitions}")

        # Collect all info into system_info
        system_info = {
            "user": user,
            "pc_name": pc_name,
            "os": os_info,
            "processor": processor,
            "ram": ram,
            "ip_address": ip_address,
            "mac_address": mac_address,
            "boot_time": boot_time,
            "partitions": partitions
        }

        print(f"System information collected: {system_info}")
        return system_info
    except Exception as e:
        print(f"Error gathering system information: {e}")
        return None

def get_ip_address():
    hostname, _, ip_list = socket.gethostbyname_ex(socket.gethostname())
    ip_address = ip_list[0] if ip_list else "No IP Found"
    print(f"IP Address: {ip_address}")
    return ip_address

def get_mac_address():
    mac_address = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
    print(f"MAC Address: {mac_address}")
    return mac_address

def get_partitions():
    partitions_list = []
    partitions = psutil.disk_partitions()
    print(f"Found partitions: {[p.device for p in partitions]}")
    for partition in partitions:
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError as e:
            partition_info = {
                "device": partition.device,
                "error": str(e)
            }
            print(f"Permission error on partition {partition.device}: {str(e)}")
        else:
            partition_info = {
                "device": partition.device,
                "total_size": get_size(partition_usage.total),
                "used": get_size(partition_usage.used),
                "free": get_size(partition_usage.free),
                "percentage": partition_usage.percent
            }
            print(f"Partition info: {partition_info}")
        partitions_list.append(partition_info)
    return partitions_list

def send_to_firestore(data):
    try:
        # Connect to Firestore and add the data to the 'system_info' collection
        firestore_db = firestore.client()
        doc_ref_tuple = firestore_db.collection("system_info").add(data)

        # Extract the DocumentReference from the returned tuple
        doc_ref = doc_ref_tuple[1]  # The DocumentReference is the second element of the tuple

        # Print the ID of the document saved to Firestore
        print(f"Data saved to Firestore with ID: {doc_ref.id}")
        return True  # Indicate success
    except Exception as e:
        print(f"Failed to send data to Firestore: {e}")
        return False  # Indicate failure

def show_message(success):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    if success:
        messagebox.showinfo("Success", "System information collected and sent successfully.")
    else:
        messagebox.showerror("Error", "Failed to collect or send system information.")
    root.destroy()  # Close the Tkinter window

def collect_system_info():
    try:
        print("Collecting system information...")
        # Collect system information and add a timestamp
        system_info = System_information()
        system_info["collected_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save the data to Firestore
        success = send_to_firestore(system_info)

        # Show message based on success
        show_message(success)
    except Exception as e:
        print(f"Error: {e}")
        show_message(False)  # Show error message if exception occurs

if __name__ == "__main__":
    try:
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Starting the program...")
        collect_system_info()
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Program completed.")
    except Exception as e:
        print(f"Unhandled exception: {e}")
        traceback.print_exc()  # Print the stack trace to see where the error occurred
        show_message(False)  # Show error message if unhandled exception occurs
