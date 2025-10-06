# MonitoringSystem
This is the main repo for the fridge monitoring system for the LA Solar Fridge group.

# Software 
The software is designed to run on a Raspberry Pi Zero/W/2

## Getting started

install the dependencies in requirements.txt `pip install -r requirements.txt`

add the airtable API key to the Raspberry Pis .bashrc `export AIRTABLE_API_KEY="LONG_API_STRING_HERE"` 

The API string should not be made public, contact the airtable administrators to get the API string.

#TODO(Heidt) add instructions here to get the API key

add the fridge ID to the Raspberry Pis .bashrc `export FRIDGE_ID="FRIDGE_ID_STRING_HERE"`

The fridge ID string can be acquired by running `python airtable.py` which will print out a list of fridges.
Copy the id field to the `FRIDGE_ID_STRING_HERE` part of the export statement.
