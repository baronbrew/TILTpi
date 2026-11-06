# Tilt Cloud Logging API

This document describes the HTTP POST format used by Tilt devices and apps when logging to a custom Cloud URL.

## Compatibility

These specifications apply to:
- **Tilt Pi**
- **iOS and Android Tilt apps** (all versions)
- **Tilt Pico**

## Request Format

The client sends an HTTP `POST` with `Content-Type: application/x-www-form-urlencoded; charset=utf-8`.

### Fields

| Field      | Description                                      | Units / Format                                      | Notes |
|------------|--------------------------------------------------|-----------------------------------------------------|-------|
| `Timepoint` | Timestamp of the reading                        | Google Sheets / Excel serial date (days since 1899-12-30, fractional day = time) | Device’s **local** time. Convert to Unix timestamp (seconds since 1970-01-01 UTC) with: `(Timepoint - 25569) * 86400`. In JavaScript: `new Date((Timepoint - 25569) * 86400 * 1000)`. |
| `Temp`     | Temperature                                     | Degrees Fahrenheit (°F)                             | Always °F, regardless of app display units |
| `SG`       | Specific gravity                                | SG (e.g. `1.045`)                                   | Always SG, not Plato. Standard Tilt typically 3 decimals; Tilt Pro typically 4 |
| `Beer`     | Beer / batch name                               | String                                              | User-entered name |
| `Color`    | Tilt color                                      | String                                              | One of: `RED`, `GREEN`, `BLACK`, `PURPLE`, `ORANGE`, `BLUE`, `YELLOW`, `PINK`. May optionally be followed by a colon and MAC address (e.g. `ORANGE:f9:15:82:6f:de:27`) when the “Identify by MAC” feature is enabled in the app. |
| `Comment`  | Optional comment or control string              | String                                              | Usually empty. When a new log is started, may contain an email address or an “@” symbol (used by the Google Sheets backend to create a new sheet — these should be ignored by third-party endpoints). May also contain a JSON-formatted string specifying preferred units (e.g. gravity and temperature units). The JSON form only appears on the first post when a log is started, not on subsequent regular readings. |

### Example Payload

Timepoint=43331.79300001158&Temp=65.0&SG=1.01&Beer=Munich%20Lager%20%231&Color=PINK&Comment=text

## Server Response

The endpoint should respond with HTTP `200` and a JSON body of the form:

{ "result": "success" }

The string "success" is displayed in the Tilt app’s status message. Other values (or non-JSON responses) will still be accepted as long as the HTTP status is 200, but only the "success" string is shown to the user.Important Behavior Notes
Units are standardized: Temp is always sent in °F and SG is always sent as specific gravity, regardless of the units selected in the app.
Precision: Standard Tilt devices typically report SG to 3 decimal places. Tilt Pro devices typically report to 4 decimal places.
Timepoint uses the device’s local time, encoded as a Google Sheets serial date.
Retries: The apps do not aggressively retry failed posts. Returning HTTP 200 prevents retry loops.
Redirects: Follow standard HTTP redirect behavior.