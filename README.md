# MonitoringSystem
This is the main repo for the fridge monitoring system for the LA Solar Fridge group.

# Software 
The software is designed to run on a Raspberry Pi Zero/W/2

## Getting started

### Install dependencies
install the dependencies in requirements.txt `pip install -r requirements.txt`

### Setup Airtable
add the airtable API key to the Raspberry Pis .bashrc `export AIRTABLE_API_KEY="LONG_API_STRING_HERE"` 

The API string should not be made public, contact the airtable administrators to get the API string.

#TODO(Heidt) add instructions here to get the API key

add the fridge ID to the Raspberry Pis .bashrc `export FRIDGE_ID="FRIDGE_ID_STRING_HERE"`

The fridge ID string can be acquired by running  `python airtable.py` which will print out a list of fridges.
Copy the id field to the `FRIDGE_ID_STRING_HERE` part of the export statement.

### Setup Google Drive

for the google drive API, follow the instructions here to get started: https://developers.google.com/workspace/drive/api/quickstart/python

You'll only need to do this once (#TODO(Heidt) confirm) and then you can re-use the credentials.

You'll also need to add your email as a test user. Go to the Oauth consent screen. Then in the left menu select audience. In the test users section add your username.

#TODO(Heidt) the project "Branding" needs to be set to external if there isn't a google cloud account, not sure if that's dangerous or not, need to confirm safety.

Create a new directory in your home directory called Credentials. Move the credentials.json file to this directory. In your .bashrc add a line `export FRIDGE_GDRIVE_CREDENTIALS="/path/to/credentials.json"` where /path/to is the full path to where you saved this file.

If this is the first time you're running this, you may need to run the google_drive.py file to authorize the application. Call `python google_drive.py`. This requires a browser to be opened up to do, so if you're doing this on the Pi, make sure you have VNC setup or you're running with a monitor connected.