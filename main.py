from typing import List, Tuple
import json

from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.service import BleakGATTService
import asyncio


"""
Given a list of devices we want to prompt the user for a device and validate the selection

:param devices: List of devices that were discovered
"""
def selectDevice(devices):
    selectedDevice = -1

    # Until we have made a valid selection we want to keep prompting for a selection
    while selectedDevice == -1:
        try:
            selection = int(input("Select the device to connect to: "))
        except ValueError as e:
            print(f"An error occurred when parsing your input: {e}")
            continue
        
        if selection > 0 and selection <= len(devices):
            selectedDevice = selection
        else:
            print("Invalid selection")

    # Subtract one to turn our selection back into an index
    return selectedDevice-1

"""
Add an API key to the connected device
"""
async def addAPIKey(client, apiService):
    apiKey = input("API Key: ")
    endpoint = input("Endpoint: ")
    port = int(input("Port: "))
    request = {
        "apiKey": apiKey,
        "endpoint": endpoint,
        "port": port
    }
    await client.write_gatt_char(apiService.get_characteristic("abc1").uuid, json.dumps(request).encode('utf-8'))

"""
Test the API key currently configured on the device
"""
async def testAPIKey(client, apiService):
    for _ in range(2):
        try:
            result = (await client.read_gatt_char(apiService.get_characteristic("abc1").uuid)).decode('utf-8')
            if str(result) == "True":
                print("Successfully contacted API!")
            else:
                print("Failed to contact API please resend the credentials and ensure you are connected to Wi-Fi.")
            break
        except Exception as e:
            print(f"An error occurred reading characteristic: {e}, retrying...")

"""
Disconnect from the specified WiFi network
"""
async def connectToWiFi(client, wifiService):
    ssid = input("Enter the SSID to disconnect from: ")
    password = input("Enter WiFi password: ")
    request = {"ssid": ssid, "password": password}

    await client.write_gatt_char(wifiService.get_characteristic("31415924535897932384626433832792").uuid, json.dumps(request).encode('utf-8'))
    print("Command sent!")

"""
Disconnect from the specified WiFi network
"""
async def disconnectWiFi(client, wifiService):
    ssid = input("Enter the SSID to disconnect from: ")
    request = {"ssid": ssid}

    await client.write_gatt_char(wifiService.get_characteristic("31415924535897932384626433832794").uuid, json.dumps(request).encode('utf-8'))
    print("Command sent!")

"""
Get the current status of our internet connection
"""
async def getConnectionStatus(client, wifiService):
    for _ in range(2):
        try:
            result = (await client.read_gatt_char(wifiService.get_characteristic("31415924535897932384626433832791").uuid)).decode('utf-8')
            print(result)
            break
        except Exception as e:
            print(f"An error occurred reading characteristic: {e}, retrying...")

"""
Scan the bluetooth devices in range returning a list of all devices with a name
"""
async def scanDevices() -> List[BLEDevice]:
    print("Scanning for devices this may take up to 20 seconds...")

    # For all the devices down only output those that have a name
    deviceCount = 0
    validDevices = []
    retries = 0
    while deviceCount <= 0 and retries < 3:
        # Scan for devices with a 20 second timeout
        devices = await BleakScanner.discover(timeout=20)
        print("Discovered Devices:")
        for device in devices:
            if device.name != None: 
                validDevices.append(device)
                deviceCount += 1
                print(f"\t {deviceCount}: {device.name} : {device.address}")
        if deviceCount <= 0:
            print("\tNo devices found rescanning...")
            retries += 1

    print("")
    return validDevices

"""
Connect to a given bluetooth client and return the services we would like to interact with

:param device: The device we wish to connect to
"""
async def connectToClient(device: BLEDevice):
    client = BleakClient(device.address)
    for i in range(3):
        print(f"{i+1}/3 - Attempting to connect to {device.name} : {device.address}")
        try:
            await client.connect()
            break
        except Exception as e:
            print(f"Connection failed: {e}, retrying...")
    print(f"Connected to {device.name}!")


    # # Get the API service
    apiService = client.services.get_service("abc0")
    wifiService = client.services.get_service("31415924535897932384626433832790")

    return (client, apiService, wifiService)
    
"""
Handle the options to interact with the API components of the device
"""
async def apiOptions(client, apiService):
    print("")
    print("1: Transmit API Keys")
    print("2: Test API Keys")

    match int(input("Select an action: ")):
        case 1:
            await addAPIKey(client, apiService)
        case 2:
            await testAPIKey(client, apiService)
       
"""
Handle the options to interact with the WiFi components of the device
"""
async def wiFiOptions(client, wifiService):
    print("")
    print("1: Connect device to Wi-Fi Network")
    print("2: Test Wi-Fi Connection")
    print("3: Remove Wi-Fi Network from device")

    match int(input("Select an action: ")):
        case 1:
            await connectToWiFi(client, wifiService)
        case 2:
            await getConnectionStatus(client, wifiService)
        case 3:
            await disconnectWiFi(client, wifiService)

"""
Now that we have connected to the device we should show a different menu
"""
async def deviceMenu(client: BleakClient, apiService: BleakGATTService, wifiService: BleakGATTService):
    connected = True
    while connected:
        print("1: Wi-Fi Options")
        print("2: API Key Options")
        print("3: Debug Options")
        print("4: Disconnect")

        match int(input("Select an action: ")):
            case 1:
                await wiFiOptions(client, wifiService)
            case 2:
                await apiOptions(client, apiService)
            case 3:
                print("Not implemented")
            case 4:
                await client.disconnect()
                connected = False

async def main():
    print("Binsight Bluetooth Configuration Utility")
    print("Version 1.0")
    print("Author: Will Richards\n")

    # Scan and select a given device
    devices = await scanDevices()
    if len(devices) > 0:
        selectedDevice = devices[selectDevice(devices)]

        # Retrieve the services running our characteristics
        client, apiService, wifiService = await connectToClient(selectedDevice)
        if(client.is_connected):
            await deviceMenu(client, apiService, wifiService)
        else:
            print("Unable to connect to device.")
    else:
        print("No devices found after 3 retries")

if __name__ == "__main__":
    asyncio.run(main())