# Tilt Pi Installation Instructions for Raspbian Jessie or Stretch

## Note: for Mac OS X installation see: (credit: Bruce Morgan)
[Tilt Pi Instructions for Mac OS X](./TILTpi#tilt-pi-installation-instructions-for-mac-os-x)

## Update March 20, 2018
Due to an updated nodejs version used in the script "update-nodejs-and-nodered", the bleacon scanning node will fail to install. A workaround is to manually install node package manager, "npm" and then install a version manager "n" for nodejs so that nodejs version 4.x can be installed first before installing bleacon. Once bleacon and dashboard UI are installed, nodejs and node-red can be updated.

## Step 1
Using SSH from another computer or from a Raspberry Pi directly, open a command line window to enter the following commands. Install node package manager, "npm".

`sudo apt-get update`

`sudo apt-get install npm`

## Step 2
Install nodejs version manager, "n".

`sudo npm install n -g`

## Step 3
Install nodejs version 4.8.7 (this version will work with bleacon)

`sudo n 4.8.7`

## Step 4
Install bleacon, an iBeacon scanning node for Node-Red. Note: Tilt uses iBeacon format to broadcast data so any device that can scan for iBeacons can connect to it.

`sudo npm install node-red-contrib-bleacon -g`

## Step 4
Install dashboard UI for Node-Red.

`sudo npm install node-red-dashboard -g`

## Step 5
Update node-red and nodejs using the script provided by nodered.org. [Raspberry Pi specific Node-Red install instructions for Raspbian Jessie](https://nodered.org/docs/hardware/raspberrypi).

`bash <(curl -sL https://raw.githubusercontent.com/node-red/raspbian-deb-package/master/resources/update-nodejs-and-nodered)`

Note: Answer `yes` to installing Raspberry Pi specific nodes.

## Step 6
Set Node-Red to start on system start up.

`sudo systemctl enable nodered.service`

## Step 7
Download Tilt Pi “flow” from Baron Brew GitHub account to Raspberry Pi

`wget -O /home/pi/flow.json https://raw.githubusercontent.com/baronbrew/TILTpi/master/flow.json`

## Step 8
Reboot Raspberry Pi. Node-red will start at boot.

`sudo reboot`

## Step 9
Run downloaded Tilt Pi app/flow in Node-Red:

`curl -X POST http://localhost:1880/flows -H "Content-Type: application/json" -H "Node-RED-Deployment-Type: nodes" --data "@/home/pi/flow.json"`

## Step 10

In a web browser visit `http://tiltpi.local:1880/ui` or `http://localhost:1880/ui`. If this doesn't work, you may need to find the IP address of your Raspberry Pi and go to `http://X.X.X.X:1880/ui` where `X.X.X.X` is your Raspberry Pi's IP address.

# Tilt Pi Installation Instructions for Mac OS X

## 1. 

From an account on the Mac with Admin privileges install HomeBrew:

`/usr/bin/ruby -e "$(/usr/bin/curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`

This will install Xcode command line tools if it is not already installed.

## 2. 

Install the Node Package Manager:

`/usr/local/bin/brew install npm`

## 3. 

Install nodejs version manager, "n":

`sudo /usr/local/bin/npm install n -g`

## 4. 

Install nodejs ver 4.8.7:

`sudo /usr/local/bin/n 4.8.7`

## 5. 

Install the bleacon agent that listens to bluetooth:

`sudo /usr/local/bin/npm install node-red-contrib-bleacon -g`

## 6.

Install node-red dashboard:

`sudo /usr/local/bin/npm install node-red-dashboard -g`

## 7. 

Create a user "pi" from System Preferences-> Users & Groups. Unlock first then click on “+”:

New Account: `Standard`
Full Name: `Tilt`
Account Name: `pi`

**Important:** Click NO to admin privileges !! and create a password for that user. Write the password down as you will need it to login as user "pi".

## 8. 

From the desktop open the Finder. Go to Applications->Utilities and run Terminal. Login as user "pi" using the password you created in the Terminal window

`login pi`
Password: `******` (enter password created in Step 7)

## 9. 

As user "pi" within that terminal download Tilt Pi “flow” from Baron Brew GitHub account. Note that this has static file references which are used on the Raspberry Pi and these need to be deleted.

### a. 

Get the file:

`/usr/bin/curl -o  flow.json https://raw.githubusercontent.com/baronbrew/TILTpi/master/flow.json`

### b. 

Make a copy of it:

`cp flow.json flow.json.orig`

### c. 

Then use sed to strip the static file references:

`cat flow.json.orig | sed 's/\/home\/pi\///g' > flow.json`

## 10. 

As user pi from that terminal run node-red from user account pi and background it:

`/usr/local/bin/node-red &`

## 11. 

From the pi home account (you can either use the same window or create another terminal window and login as user "pi" again) run the following to create the Tilt flow:

`/usr/bin/curl -X POST http://localhost:1880/flows -H "Content-Type: application/json" -H "Node-RED-Deployment-Type: nodes" --data "@flow.json"`

## 12. 

Use a web browser (Chrome or Firefox) to visit `http://localhost:1880/ui` or `http://127.0.0.1:1880/ui`
You should be able to see the Tilts if they are on and within range.