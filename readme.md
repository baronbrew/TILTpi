# Tilt Pi Installation Instructions for Raspbian Jessie
## Step 1
Using SSH from another computer or from a Raspberry Pi directly, open a command line window to install Node-Red per [Raspberry Pi specific Node-Red install instructions for Raspbian Jessie](https://nodered.org/docs/hardware/raspberrypi).

Basically, you will copy/paste the following command and press enter. This will take about 15 minutes to complete.

`bash <(curl -sL https://raw.githubusercontent.com/node-red/raspbian-deb-package/master/resources/update-nodejs-and-nodered)`

Note: Answer `yes` to installing Raspberry Pi specific nodes.
## Step 2
Set Node-Red to start on system start up.

`sudo systemctl enable nodered.service`

## Step 3
Install bleacon, an iBeacon scanning node for Node-Red. Note: Tilt uses iBeacon format to broadcast data so any device that can scan for iBeacons can connect to it.

`sudo npm install node-red-contrib-bleacon -g`

## Step 4
Install dashboard UI for Node-Red.

`sudo npm install node-red-dashboard -g`

## Step 5
Download Tilt Pi “flow” from Baron Brew GitHub account to Raspberry Pi

`wget -O /home/pi/flow.json https://raw.githubusercontent.com/baronbrew/TILTpi/master/flow.json`

## Step 6
Reboot Raspberry Pi.

`sudo reboot`

## Step 7
Run downloaded Tilt Pi app/flow in Node-Red:

`curl -X POST http://localhost:1880/flows -H "Content-Type: application/json" -H "Node-RED-Deployment-Type: nodes" --data "@/home/pi/flow.json"`

## Step 8

In a web browser visit `http://tiltpi.local:1880/ui` or `http://localhost:1880/ui`. If this doesn't work, you may need to find the IP address of your Raspberry Pi and go to `http://X.X.X.X:1880/ui` where `X.X.X.X` is your Raspberry Pi's IP address.