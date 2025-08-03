//  Setup Instructions (continued):
//
//  For Google Sheets to receive data from the Tilt app
//  deploy script as web app from the "Publish" menu and set permissions. Note that you are now the owner and "developer" of the app.
//
//  1) Got to "Publish" menu and select "Deploy as web app..."
//   
//  2) In the dialog box, set "Who has access to the app:" to "Anyone, even anonymous" and click "Deploy".
//
//  3) A dialog box will appear. Select "Review Permissions". Another dialog box will appear. Select your Google Account.
//
//  4) A dialog box with "This app isn't verified" will appear. Select "Advanced" then select "Go to Tilt Cloud Template for Tilt App 1.6+ (unsafe)"
//
//  5) A dialog box with permission requests will appear. Select "Allow".
//
//  6) A dialog box confirming the app has been published will appear. Note: Do NOT use the cloud URL shown in the dialog, see next step.
//
//  7) Close Google Scripts tab and return to Google Sheets. Use the new "Tilt" menu to email yourself the cloud URL.

var SHEET_NAME = "Data";
var SCRIPT_PROP = PropertiesService.getScriptProperties(); // new property service

// If you don't want to expose either GET or POST methods you can comment out the appropriate function
function doGet(e){
  return ContentService
  .createTextOutput("Enter the following link into the Cloud URL settings (under the gear icon in iOS/Android app):" + ScriptApp.getService().getUrl())
          .setMimeType(ContentService.MimeType.TEXT);
}

function doPost(e){
  return handleResponse(e);
}

//used for testing without a Tilt
function testBeer(){
  var e = {
  "parameter": {
  "Beer": "Test",
  "Temp": 64,
  "SG":1.045,
  "Color":"BLUE",
  "Comment":"noahbaron@gmail.com",
  "Timepoint":44160.11
  }
  };
  handleResponse(e);
}

function handleResponse(e) {
  try {
    // next set where we write the data - you could write to multiple/alternate destinations 
    var masterDoc = SpreadsheetApp.openById(SCRIPT_PROP.getProperty("key"));
    var beersSheet = masterDoc.getSheetByName("Beers");
    var nextBeerRow = (beersSheet.getLastRow()+1).toFixed(0);
    //app expects beer name to be followed by a comma and beer ID (except for new beers)
    var beerName = e.parameter.Beer.split(",");
    var tiltColor= e.parameter.Color;
    var comment = e.parameter.Comment;
    var email = null;
    var doclongURL = "";
    var beerId = null;
    var doc = null;
    //if beer name is blank, give beer a default name
    if (beerName[0] == "") {
      beerName[0] = "Untitled";
    }
    //if beer number is blank, probably a new beer and check if email address in comment
    if (beerName[1] !== undefined){
    var beerIds = beersSheet.getRange("A" + beerName[1] + ":" + "C" + beerName[1]).getValues();
       //get Sheets ID if beer name matches
      if (e.parameter.Beer.toLowerCase() == beerIds[0][0].toLowerCase()) {
            beerId = beerIds[0][1];
        }
     }
    //check if this is a new beer and process as needed
    if(beerId == null){
      //check if comment field has an @ symbol for an email address
      if (comment.indexOf("@") > -1){
      //prevent simultaneous writes
      var lock = LockService.getScriptLock();
      lock.waitLock(60000);
      nextBeerRow = (beersSheet.getLastRow()+1).toFixed(0);
      var settingsSheet = masterDoc.getSheetByName("Settings");
      var sheetTemplate = settingsSheet.getRange("B1").getValue();
      var driveTemplate = DriveApp.getFileById(sheetTemplate); //file ID of template
      var driveDoc = driveTemplate.makeCopy(beerName[0] + " (" + tiltColor + " TILT)");
      driveDoc.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
      doc = SpreadsheetApp.open(driveDoc);
      beerId = doc.getId();
      doclongURL = doc.getUrl();
      beerName[1] = nextBeerRow;
      try { 
      driveDoc.addEditor(comment);
      sharedWith = comment + '<br>Important: Check email for invitation to edit if not a Gmail address.';
      var editors = doc.getEditors();
      MailApp.sendEmail({to : comment,
                         replyTo : "info@baronbrew.com",
                         subject : "Tilt™ Hydrometer Log for " + beerName[0],
                         body : 'View and edit your data here with Google Sheets: ' + doclongURL + " To log data to the same sheet using another device, enter the following name as your beer name: " + beerName.toString() + " (Be sure to include comma and number afterward.)",
                         name : "Tilt Customer Service",
                        });                
      e.parameter.Comment = "";
      }
      catch (shareError) { 
      sharedWith = 'View access only. (Gmail address not entered.)';
      }
      finally {
        //send email to non-gmail account
      if ( sharedWith == 'View access only. (Gmail address not entered.)' && comment != '@' ) {
      MailApp.sendEmail({to : comment,
                         replyTo : "info@baronbrew.com",
                         subject : "Tilt™ Hydrometer Log for " + beerName[0],
                         body : 'View your data here with Google Sheets (edit access requires a Gmail account): ' + doclongURL + " To log data to the same sheet using another device, enter the following name as your beer name: " + beerName.toString() + " (Be sure to include comma and number afterward.)",
                         name : "Tilt Customer Service",
                     });
      e.parameter.Comment = "";
      }
        if ( comment == '@' ) {
          e.parameter.Comment = "";
        }
      //add beer to 'Beers' tab
      var beerNameString = beerName.join();
      beersSheet.appendRow([beerNameString,beerId,doc.getUrl()]);
      //work around in case a number is entered as a beer name
      beersSheet.getRange("A" + nextBeerRow).setNumberFormat('@STRING@');
      beersSheet.getRange("A" + nextBeerRow).setValue(beerNameString);
      SpreadsheetApp.flush();
      lock.releaseLock();
      }
    }
      else{
       //advise user to enter email into comment field
      return ContentService
      .createTextOutput(JSON.stringify({result:beerName[0] + "<br><strong>TILT | " + tiltColor + '</strong><br>Start a new cloud log by entering your email address as a comment.', beername:beerName.toString(), tiltcolor:tiltColor}))
          .setMimeType(ContentService.MimeType.JSON);
    }
  }
    else{
      doc = SpreadsheetApp.openById(beerId);
      var editors = doc.getEditors();
      if ( editors.length == 1 ) {
           sharedWith = 'View access only. Check email for invitation to edit.';
      } else {
        sharedWith = editors[1].getEmail();
      }
      doclongURL = doc.getUrl();
      //check if comment field has a web address prefix used to transmit link to raspberry pi
      if (comment.indexOf("http") > -1){
        MailApp.sendEmail({to : editors[1].getEmail(),
                         replyTo : "info@baronbrew.com",
                         subject : "Tilt™ Pi Setup Complete",
                         body : "You may now access your Tilt Pi from your local WiFi network at http://tiltpi.local:1880/ui or at the following address: " + comment,
                         name : "Tilt Customer Service",
                        });
        e.parameter.Comment = "";
      }
    }
    var sheet = doc.getSheetByName("Data");    
    e.parameter.Beer = beerName[0]; //remove beer name unique identifier when posting to sheet
    // we'll assume header is in row 1 but you can override with header_row in GET/POST data
    var headRow = e.parameter.header_row || 1;
    var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    var nextRow = sheet.getLastRow()+1; // get next row
    var row = []; 
    // loop through the header columns
    for (i in headers){
      if (headers[i] == "Timestamp"){ // special case if you include a 'Timestamp' column
        row.push(new Date());
      } else { // else use header name to get data
        row.push(e.parameter[headers[i]]);
      }
    }
    sheet.getRange(nextRow, 1, 1, row.length).setValues([row]);
    // return success results
    return ContentService
    .createTextOutput(JSON.stringify({result: beerName.toString() + '<br><strong>TILT | ' + tiltColor + '</strong><br>Success logging to the cloud. (row: ' + nextRow + ')<br><a class="link external" href="' + doclongURL + '">View Cloud Log</a><br>Edit access: ' + sharedWith, beername:beerName.toString(), tiltcolor:tiltColor, doclongurl:doclongURL}))
    .setMimeType(ContentService.MimeType.JSON);
  } catch(e){
    // if error return this
    return ContentService
    .createTextOutput(JSON.stringify({result: JSON.stringify(e), error: e}))
    .setMimeType(ContentService.MimeType.JSON);
  } finally { //release lock if it still exists
    if (lock !== undefined){
     SpreadsheetApp.flush();
     lock.releaseLock();
    }
}
}


function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Tilt')
    .addItem('View Cloud URL', 'menuItemURL')
    .addItem('Email Cloud URL', 'menuItemEmailURL')
    .addToUi();
  if(SCRIPT_PROP.getProperty("url") == null){
    setup();
  }
}

function setup() {
  var doc = SpreadsheetApp.getActiveSpreadsheet();
  SCRIPT_PROP.setProperty("key", doc.getId());
}

function menuItemURL() {
    SCRIPT_PROP.setProperty("url", ScriptApp.getService().getUrl());
     SpreadsheetApp.getUi()
      .alert("Copy/Paste the following URL into the Cloud URL field in the Tilt app settings: " + ScriptApp.getService().getUrl());  
}

function menuItemEmailURL(){
    SCRIPT_PROP.setProperty("url", ScriptApp.getService().getUrl());  
    MailApp.sendEmail(Session.getActiveUser().getEmail(), 'Tilt Cloud URL', "Copy/Paste the following URL into the Cloud URL field in the Tilt app settings: " + ScriptApp.getService().getUrl());
    SpreadsheetApp.getUi()
      .alert("Email sent to: " + Session.getActiveUser().getEmail());
}
  
  function updateChart(){
    //currently unused - update minimum values in chart to set appropriate range based on units preferred. Run when new sheet created.
  var reportSheet = doc.getSheetByName("Report");
  var chartSheet = doc.getSheetByName("Chart");
  var gravityUnits = reportSheet.getRange("B6").getValue();
  var tempUnits = reportSheet.getRange("B5").getValue();
  var chart = chartSheet.getCharts()[0];
  if (gravityUnits == "SG"){
    var gMin = 0.990;
  }else{
    var gMin = -5.0;
  }
  if (tempUnits == "Fahrenheit"){
    var tempMin = 25;
  }else{
    var tempMin = -5;
  }
  chart = chart.modify()
  .asLineChart()
  .setOption('vAxes', {0 : {viewWindow : {min: gMin}}, 1 : {viewWindow: {min: tempMin}}})
  .build();
  chartSheet.updateChart(chart);
   }