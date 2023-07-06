# This is Traveller Trade Tool for Mongoose Traveller 2e and other 2d6 rules

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import json
import random
import requests


# Example string
# worldInfo = '{"Worlds":[{"Name":"Gollere","Hex":"1305","UWP":"D574756-7","PBG":"720","Zone":"","Bases":"","Allegiance":"NaHu","Stellar":"F5 V","SS":"B","Ix":"{ -1 }","CalculatedImportance":-1,"Ex":"(967-2)","Cx":"[6646]","Nobility":"","Worlds":6,"ResourceUnits":-756,"Subsector":1,"Quadrant":0,"WorldX":-116,"WorldY":-35,"Remarks":"Ag Pi","LegacyBaseCode":"","Sector":"Trojan Reach","SubsectorName":"Egyrn","SectorAbbreviation":"Troj","AllegianceName":"Non-Aligned, Human-dominated"}]}'
worldInfo = '{"Worlds":[{"Name":"Tarkine","Hex":"1434","UWP":"C566662-7","PBG":"310","Zone":"A","Bases":"S","Allegiance":"CsIm","Stellar":"M0 V M2 V","SS":"N","Ix":"{ 0 }","CalculatedImportance":0,"Ex":"(854-4)","Cx":"[2613]","Nobility":"","Worlds":9,"ResourceUnits":-640,"Subsector":13,"Quadrant":4,"WorldX":-115,"WorldY":-46,"Remarks":"Ag Ni Ri Da O:1435","LegacyBaseCode":"S","Sector":"Spinward Marches","SubsectorName":"District 268","SectorAbbreviation":"Spin","AllegianceName":"Client state, Third Imperium"}]}'
starPortInfo = '{"Starport":[{"Class":"A","Quality":"Exellent","Berthing":"1d6*1000","Fuel":"Refined (Cr500/ton)","Facilities":"Shipyard (all) - repairs"},{"Class":"B","Quality":"Good","Berthing":"1d6*500","Fuel":"Refined (Cr500/ton)","Facilities":"Shipyard (spacecraft) - repairs"},{"Class":"C","Quality":"Routine","Berthing":"1d6*100","Fuel":"Unrefined (Cr100/ton)","Facilities":"Shipyard (smallcraft) - repairs"},{"Class":"D","Quality":"Poor","Berthing":"1d6*10","Fuel":"Unrefined (Cr100/ton)","Facilities":"Limited repairs"},{"Class":"E","Quality":"Frontier","Berthing":"Free","Fuel":"-","Facilities":"-"},{"Class":"X","Quality":"Non","Berthing":"-","Fuel":"-","Facilities":"-"}]}'

# Convert the string into a dictionary
worlds = json.loads(worldInfo)
starports = json.loads(starPortInfo)

# Define a dictionary of modifiers depending on the hex value
diceModStd_dict = {
    "0": -3,
    "1": -2,
    "2": -2,
    "3": -1,
    "4": -1,
    "5": -1,
    "6": 0,
    "7": 0,
    "8": 0,
    "9": 1,
    "A": 1,
    "B": 1,
    "C": 2,
    "D": 2,
    "E": 2,
    "F": 3
}

taskEffectMod_dict = {
    "<-6": -3,
    "-5": -2,
    "-4": -2,
    "-3": -2,
    "-2": -2,
    "-1": -1,
    "0": 0,
    "1": 1,
    "2": 1,
    "3": 1,
    "4": 1,
    "5": 1,
    ">6": 2
}

# Define World Zones
worldZones_dict = {
    "A": 'Amber Zone',
    "R": 'Restricted'
}

worldBases_dict = {
    "S": 'Scout Base',
    "N": 'Naval Base',
    "W": 'Scout Way Station',
    "D": 'Naval Depot',
    "Z": 'Zhodani',
    "R": 'Research Station',
    "X": 'Prison, Exile Camp',
    "P": 'Penal Colony'
}

# Test code for reading json string from TravellerMap.com, API call for world information
worldName = worlds["Worlds"][0]["Name"]
worldHex = worlds["Worlds"][0]["Hex"]
worldUWP = worlds["Worlds"][0]["UWP"]
worldBases = worlds["Worlds"][0]["Bases"]
worldZone = worlds["Worlds"][0]["Zone"]
worldRemarks = worlds["Worlds"][0]["Remarks"]
worldAllegiance = worlds["Worlds"][0]["Allegiance"]
worldSector = worlds["Worlds"][0]["Sector"]
worldSubSector = worlds["Worlds"][0]["SubsectorName"]

# expand UWP to separate variables
uwpStarport = worldUWP[0]
uwpSize = worldUWP[1]
uwpAtmo = worldUWP[2]
uwpHydro = worldUWP[3]
uwpPop = worldUWP[4]
uwpGov = worldUWP[5]
uwpLaw = worldUWP[6]
uwpTL = worldUWP[8]

# expanding UWP numbers
# Define the class to search for
targetClass = uwpStarport.upper()
targetZone = worldZone

# Find the dictionary that corresponds to the targetClass
targetDict = next((item for item in starports['Starport'] if item['Class'] == targetClass), None)

# Extract the possible range of values for the "Berthing" attribute of the targetClass
berthingRange = targetDict['Berthing']

# worldZoneCurrent = next((item for item in worlds['Worlds'] if item['Zone'] == targetZone), None)
worldZoneCurrent = worldZones_dict.get(worldZone, 0)
worldBasesCurrent = worldBases_dict.get(worldBases, 0)

# RANDOMISING STUFF #
# ================= #
# berthing = random.randint(1, int(berthingRange.split('d')[1])) * int(berthingRange.split('*')[0])
berthing = random.randint(1,6) * int(berthingRange.split('*')[1])

# API CALL TESTS

# Set the base URL for the API call
url = "https://travellermap.com/api"

# Set the parameters for the API call
params = {
    "density": "full",
    "size": "1024",
    "jump": "3",
    "format": "json"
}

# Make the API call and store the response in a variable
response = requests.get(url + "/map", params=params)

# Check if the response was successful (status code 200)
if response.status_code == 200:
    # Get the JSON data from the response
    data = response.json()

    # Print the world information for each world in the data
    for world in data["worlds"]:
        print("World:", world["name"])
        print("UWP:", world["uwp"])

    # Print the URL of the generated map image
    print("Map URL:", data["mapurl"])
else:
    print("Error making API call:", response.status_code)




# Output tests
print(f"## {worldName}   {worldUWP} {worldBases} {worldRemarks} {worldAllegiance} {worldZoneCurrent} ({worldSubSector}/{worldSector}[{worldHex}])")
print(f"Starport:        {uwpStarport}")
# Find the entry in the "Starport" list with the matching class
for port in starports['Starport']:
    if port['Class'] == targetClass:
        # Print the information for the matching class
        # print(f"Starport Class:", port['Class'])
        print(f"        Quality:", port['Quality'])
        print(f"       Berthing: Cr{berthing}")  # Print the randomized "Berthing" value
        print(f"           Fuel:", port['Fuel'])
        print(f"     Facilities:", port['Facilities'])
print(f"World Size:      {uwpSize}")
print(f"Atmosphere Type: {uwpAtmo}")
print(f"Hydrographic %:  {uwpHydro}")
print(f"Population:      {uwpPop}")
print(f"Main Government: {uwpGov}")
print(f"Law Level:       {uwpLaw}")
print(f"Tech Level:      {uwpTL}")
print()
print(f"Expanded information:")
print(f"         Bases:  {worldBasesCurrent}")
print(f"          Zone:  {worldZoneCurrent}") #{worldZone}#
