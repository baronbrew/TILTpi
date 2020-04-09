# Tilt Pi Installation Instructions for Raspbian Buster 
## Update April 9, 2020
These instructions have been confirmed to work on February 13, 2020 version of Raspbian Buster.

## Update July 13, 2019
It appears "Bleacon" (the Bluetooth scanning module used in Tilt Pi) no longer appears to install succesfully regardless of nodejs version when installing on recent versions of Raspbian. As such, the module has been replaced with a "Aioblescan". These instructions were tested on a fresh install of the June 20, 2019 version of Raspbian Buster installed on a Raspberry Pi 0.

## Step 1
Using SSH from another computer or from a Raspberry Pi command line directly, enter the following commands. Update Raspbian packages and install python install utility, "python3-distutils".

`sudo apt-get update --allow-releaseinfo-change`

`sudo apt-get install python3-distutils`

## Step 2
Get the “aioblescan” bluetooth scanner module customized with Tilt plugin, unzip downloaded file, go to install folder, and install. Once you complete this step, you can run the command "sudo python3 -u -m aioblescan -T" to verify Tilt scanner is working. Make sure Tilt is nearby and floating if doing the test. Use "ctrl-c" to stop scanning.

`wget https://github.com/baronbrew/aioblescan/archive/master.zip`

`unzip master.zip`

`cd aioblescan-master/`

`sudo -H python3 setup.py install`

## Step 3

Install node-red update script for Raspberry Pi using version that works with Google Sheets web apps (this forked install script installs version 0.18.4 which allows following redirects of http POST requests). Answer "yes" to install Raspberry Pi specific nodes.

`bash <(curl -sL https://raw.githubusercontent.com/baronbrew/raspbian-deb-package/master/resources/update-nodejs-and-nodered)`

## Step 4

Install dashboard ui node v2.15.5 globally for node-red and enable auto-start of node-red at boot. Re-run node-red install script.

`sudo -H npm install node-red-dashboard@2.15.5 -g`

`sudo systemctl enable nodered.service`

`bash <(curl -sL https://raw.githubusercontent.com/baronbrew/raspbian-deb-package/master/resources/update-nodejs-and-nodered)`

Note: For some reason npm does not install the dashboard ui node correctly so the node-red install script must be re-run after installing to fix the installation.

## Step 5
Reboot to start node-red on boot.

`sudo reboot`

## Step 6
Download Tilt Pi “flow” that uses the new Aioblescan module

`wget -O /home/pi/flow.json https://raw.githubusercontent.com/baronbrew/TILTpi/Aioblescan/flow.json`

## Step 7
Run downloaded Tilt Pi app/flow in node-red:

`curl -X POST http://localhost:1880/flows -H "Content-Type: application/json" -H "Node-RED-Deployment-Type: nodes" --data "@/home/pi/flow.json"`

## Step 9
As an optional step, you can add a WiFi connection manager script that has a robust algorithm to maintain the WiFi connection if the connection is unstable.

`curl -L wifi.brewpiremix.com | sudo bash`

## Step 10

In a web browser visit `http://raspberrypi.local:1880/ui` or `http://localhost:1880/ui` (if not using SSH to install). If this doesn't work, you may need to find the IP address of your Raspberry Pi and go to `http://X.X.X.X:1880/ui` where `X.X.X.X` is your Raspberry Pi's IP address.
