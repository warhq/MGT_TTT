# test of api-calls to travellermap.com
import requests

# Set the base URL for the API call
url = "https://travellermap.com"

# Set the parameters for the API call
# params = {
#    "sector": "/Spiward%20Marches",
#    "subsector": "/District%20268"
#    "hex": "/1433",
#    "jump": "3",
#    "format": "json"
# }
apiCallType = "/data"
sector = "/Spinward%20Marches"
subsector = "/District%20268"
hex = "/1433"

# Make the API call and store the response in a variable
# response = requests.get(url + "/data", params=params)
response = requests.get(url + apiCallType + sector + hex + "/jump/3")

# Check if the response was successful (status code 200)
if response.status_code == 200:
    # Get the JSON data from the response
    data = response.json()

    print(data)

    # Print the world information for each world in the data
    for world in data["Worlds"]:
        print("World:", world["Name"])
        print("UWP:", world["UWP"])

    # Print the URL of the generated map image
#    print("Map URL:", data["mapurl"])
else:
    print("Error making API call:", response.status_code)
