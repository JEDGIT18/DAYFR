#Yelp modules
from __future__ import print_function
import argparse
import json
import pprint
import requests
import sys

try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode

#Discord import
import discord

#Google vision modules
import os
from google.cloud import vision
from google.cloud.vision import types
from PIL import Image
import requests

#Yelp authentication and constants
API_KEY= 'your_key'
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'
SEARCH_LIMIT = 1  


def request(host, path, api_key, url_params=None):
  """Given your API_KEY, send a GET request to the API.
  Args:
    host (str): The domain host of the API.
    path (str): The path of the API after the domain.
    API_KEY (str): Your API Key.
    url_params (dict): An optional set of query parameters in the request.
  Returns:
    dict: The JSON response from the request.
  Raises:
    HTTPError: An error occurs from the HTTP request.
  """
  url_params = url_params or {}
  url = '{0}{1}'.format(host, quote(path.encode('utf8')))
  headers = {
    'Authorization': 'Bearer %s' % api_key,
  }

  print(u'Querying {0} ...'.format(url))

  response = requests.request('GET', url, headers=headers, params=url_params)

  return response.json()

def search(api_key, term, location):
  """Query the Search API by a search term and location.
  Args:
    term (str): The search term passed to the API.
    location (str): The search location passed to the API.
  Returns:
    dict: The JSON response from the request.
  """

  url_params = {
    'term': term.replace(' ', '+'),
    'location': location.replace(' ', '+'),
    'limit': SEARCH_LIMIT
  }
  return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)

def reviews(api_key, placeID):
  return request(API_HOST, "/v3/businesses/" + placeID + "/reviews", api_key)


foodDict = {}
labelList = []
def labelsUrl(uri):
    """Detects labels in the file located in Google Cloud Storage or on the
    Web."""
    # Declare variables
    counter = 0
    global labelList

    # Declaring local objects from google cloud api
    client = vision.ImageAnnotatorClient()
    image = types.Image()
    image.source.image_uri = uri
    response = client.label_detection(image=image)
    labels = response.label_annotations

    # Adds each label to a list
    for label in labels:
        labelList.append(label.description)

    # Returns list
    return labelList

TOKEN = 'your_token'

# Initiates Discord client
client = discord.Client()

@client.event

# Function that recognizes when a message is sent and bot is online and it's been priovate messaged or mentioned in a server
async def on_message(message):

    #Variable declarations
    global labelList
    global foodDict
    isValid = False
    isNum = False
    inList = False

    # We do not want the bot to reply to itself
    if message.author == client.user:
        return

    # Command that activates bot
    if message.content.startswith('!teach'):
        # Input prompt
        msg = 'What food are you gonna teach me? (enter an image link from online)'
        await client.send_message(message.channel, msg)
        #Wait for input
        response = await client.wait_for_message()
        while response.content.isspace() or not response.content:
            response = await client.wait_for_message()
        #Set url equal to the input so we can use it later
        global url 
        url = str(response.content)
        #Store indeces of the list returned from labelsUrl method into variables
        option1 = str(labelsUrl(response.content)[0])
        option2 = str(labelsUrl(response.content)[1])
        option3 = str(labelsUrl(response.content)[2])
        #Concatenates the stored labels
        options = "Is the food one of these: " + "1. " + option1 + " 2. " + option2 + " 3. " + option3 + ". Only enter yes or no, please."
        #Sends message using the aforementioned concatenation
        await client.send_message(message.channel,  options.replace("\'",""))
        #Waits for response
        response = await client.wait_for_message()
        #Checks if the response is valid
        while response.content.isspace() or not response.content:
            response = await client.wait_for_message()
        while not isValid:
            #Checks if response is yes
            if response.content.lower().replace(" ","") == "y" or response.content.lower().replace(" ","") == "yes":
                #Asks if the identified food choices are correct
                await client.send_message(message.channel, "Which selection is the food you wanted? (enter number 1 - 3)")
                #Waits for response           
                #Conditionals for response. Adds the food item and the image url to a dictionary
                while True:
                    #Ensures number is between 1, 2, or 3
                    try:
                        response = await client.wait_for_message()
                        val = int(response.content.replace(" ",""))
                        break
                    except ValueError:
                        await client.send_message(message.channel, "Please enter a number 1 - 3!")   
                if int(response.content.replace(" ","")) == 1:
                    print(url)
                    foodDict[option1] = url
                    await client.send_message(message.channel, "Learned.")
                    labelList = []
                    isValid = True
                elif int(response.content.replace(" ","")) == 2:
                    foodDict[option2] = url
                    await client.send_message(message.channel, "Learned.")
                    labelList = []
                    isValid = True
                elif int(response.content.replace(" ","")) == 3:
                    foodDict[option3] = url
                    await client.send_message(message.channel, "Learned.")
                    labelList = []
                    isValid = True
                else:
                    await client.send_message(message.channel, "Invalid input. Try again. (enter yes or no, then enter a num 1-3")
                    labelList = []
                
            #Checks if response is no
            elif response.content.lower().replace(" ","") == "n" or response.content.lower().replace(" ","") == "no":
                #Tells the user to try again
                await client.send_message(message.channel, "I'm not smart enough right now. Try again with another picture.")
                isValid = True
                labelList = []
            else:
                #Tells the user to try again if input is invalid
                await client.send_message(message.channel, "Invalid input. Try again.")
                response = await client.wait_for_message()

    #Command that makes bot access a dictionary with food and their respective pictures        
    if message.content.startswith('!database'):
        if foodDict:
            #Loop that cycles through every key in the dictionary
            for i in foodDict:
                #Creates an embedded image and prints out the key (food) and value (picture)
                embed = discord.Embed(url = foodDict[i])
                await client.send_message(message.channel, foodDict)
                await client.send_message(message.channel, embed.url)
        else:
            await client.send_message(message.channel, "There is nothing in the database")

    #Command that makes bot recommend a restaurant using the Yelp API
    if message.content.startswith("!recommend"):
        #Checks to see if something is in our food dictionary
        if foodDict or len(foodDict) > 0:
            #Prompts user with how they would like to select food
            await client.send_message(message.channel, "How would you like to pick a food: 1. Database or 2. self-input. Please select 1 or 2")
            #Wait for a response
            response = await client.wait_for_message()
            #Checks if response is valid
            while response.content.isspace() or not response.content:
                response = await client.wait_for_message()
            while True:
                    #Ensures that response is a number
                    try:
                        response = await client.wait_for_message()
                        val = int(response.content.replace(" ",""))
                        break
                    except ValueError:
                        await client.send_message(message.channel, "Please enter a number!")   
        #Executes if food dictionary is empty                
        else:
            await client.send_message(message.channel, "Press any number to continue: ")
            response = await client.wait_for_message()
            while response.content.isspace() or not response.content:
                response = await client.wait_for_message()
            while True:
                    try:
                        response = await client.wait_for_message()
                        val = int(response.content.replace(" ",""))
                        break
                    except ValueError:
                        await client.send_message(message.channel, "Please enter a number!")  
        #Executes if response is 1 and foodDict is not empty    
        if int(response.content.replace(" ","")) == 1 and foodDict:
            #Makes a list of all foodDict keys
            keys = list(foodDict.keys())
            #Creates an empty string that we add to later
            foods =""
            #Loop that adds every key in foodDict to a string (food)
            for i in range(len(keys)):
                foods += str(i) + " " + keys[i] + " "
            await client.send_message(message.channel, "Select one of the following foods from the database: " + foods)
            while not inList:
                response = await client.wait_for_message()
                while response.content.isspace() or not response.content:
                    response = await client.wait_for_message()
                if response.content in keys:
                    food = response.content
                    inList = True
                else:
                    await client.send_message(message.channel, "Enter a food listed exactly: " + foods)
            #Yelp functionality
            await client.send_message(message.channel, "What's your location?")
            location = await client.wait_for_message()
            while location.content.isspace() or not location.content:
                location = await client.wait_for_message()
            result = search(API_KEY,food, location.content)
            rlist = result['businesses']
            rdic = rlist[0]
            name = rdic["name"]
            addressd = rdic["location"]
            address = addressd["address1"] + " " + addressd["city"] + " " + addressd["state"] + " " + addressd["zip_code"]
            rating = rdic["rating"]
            await client.send_message(message.channel, f"Here is a {food} place near {location.content}: {name}, {address}, Rating: {rating}.")

        elif int(response.content.replace(" ","")) == 2 or len(foodDict) < 1 or not foodDict:
            await client.send_message(message.channel, "What food would you like to eat?")
            food = await client.wait_for_message()
            while food.content.isspace() or not food.content:
                food = await client.wait_for_message()
            await client.send_message(message.channel, "What's your location?")
            location = await client.wait_for_message()
            while location.content.isspace() or not location.content:
                location = await client.wait_for_message()
            result = search(API_KEY,food.content, location.content)
            rlist = result['businesses']
            rdic = rlist[0]
            name = rdic["name"]
            addressd = rdic["location"]
            address = addressd["address1"] + " " + addressd["city"] + " " + addressd["state"] + " " + addressd["zip_code"]
            rating = rdic["rating"]
            await client.send_message(message.channel, f"Here is a {food.content} place near {location.content}: {name}, {address}, Rating: {rating}.")

    #Command that clears dictionary of "learned" food
    if message.content.startswith("!clear"):
        foodDict ={}
        await client.send_message(message.channel, "Database is now empty")
        
    #Command that displays the possible commands the bot can perform
    if message.content.startswith("!help"):
        await client.send_message(message.channel, "!recommend: Asks user for input and recommends a restaurant based on input.")
        await client.send_message(message.channel, "!teach: Allows the user to 'teach' the bot new foods.")
        await client.send_message(message.channel, "!database: Prints out the database of 'learned' foods the user taught the bot.")
        await client.send_message(message.channel, "!clear: Clears database of 'learned' foods.")
        await client.send_message(message.channel, "!help: Displays all possible commands and their descriptions.")

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(TOKEN)