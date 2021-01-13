# Tilt Pi Installation Instructions for Raspberry Pi OS "Buster" 
## Update January 13, 2021
These instructions have been confirmed to work on December 2, 2020 version of Raspberry Pi OS lite.

## Step 1
Using SSH from another computer or from a Raspberry Pi command line directly, enter the following commands. Update Raspbian packages and install python install utility, "python3-distutils".

`sudo apt-get update`

`sudo apt-get install python3-distutils`

## Step 2
Get the “aioblescan” bluetooth scanner module customized with Tilt plugin, unzip downloaded file, go to install folder, and install. Once you complete this step, you can run the command "sudo python3 -u -m aioblescan -T" to verify Tilt scanner is working. Make sure Tilt is nearby and floating if doing the test. Use "ctrl-c" to stop scanning.

`wget https://github.com/baronbrew/aioblescan/archive/master.zip`

`unzip master.zip`

`cd aioblescan-master/`

`sudo -H python3 setup.py install`

## Step 3

Install node-red update script for Raspberry Pi using version that works with Google Sheets web apps (this install script installs version 0.18.4 which allows following redirects of http POST requests needed for Google Sheets). Answer "yes" to install Raspberry Pi specific nodes.

`bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered) --nodered-version="0.18.4"`

## Step 4

Install dashboard ui module for node-red and enable auto-start of node-red at boot.

`cd ~/.node-red`
`sudo -H npm install node-red-dashboard@2.15.5`

`sudo systemctl enable nodered.service`

## Step 5
Reboot to start node-red on boot.

`sudo reboot`

## Step 6
Download Tilt Pi “flow” that uses the new Aioblescan module

`wget -O /home/pi/flow.json https://raw.githubusercontent.com/baronbrew/TILTpi/Aioblescan/flow.json`

## Step 7
Run downloaded Tilt Pi app/flow in node-red:

`curl -X POST http://localhost:1880/flows -H "Content-Type: application/json" -H "Node-RED-Deployment-Type: nodes" --data "@/home/pi/flow.json"`

## Step 9 (optional)
As an optional step, you can add a WiFi connection manager script that has a robust algorithm to maintain the WiFi connection if the connection is unstable.

`curl -L wifi.brewpiremix.com | sudo bash`

## Step 10

In a web browser visit `http://raspberrypi.local:1880/ui` or `http://localhost:1880/ui` (if not using SSH to install). If this doesn't work, you may need to find the IP address of your Raspberry Pi and go to `http://X.X.X.X:1880/ui` where `X.X.X.X` is your Raspberry Pi's IP address.
