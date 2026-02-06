# Google Sheet To Google Calendar Sync

This Python project automatically retrieves events from a Google Sheet and adds them to a Google Calendar.

## Features
- Connects securely to Google Sheets and Google Calendar APIs.
- Automatically detects and updates new events.
- Avoids duplicates and logs total events created.

##  Project Structure
```
project/
    ├── main.py # Entry point of the program 
    ├── config.py # Paths and credentials
    ├── AMAgoogleSheets.py # Google Sheets integration
    ├── AMAgoogleCalendar.py # Google Calendar integration
```
## Setup
1. Clone or download this repository.
2. Make sure Python 3.10+ is installed.
3. Install dependencies:
```bash
pip install gspread google-auth google-api-python-client
```
4. Place your credentials in:
```bash
NOT_SHARE/googleSheet_credentials.json
NOT_SHARE/googleCalendar_credentials.json
```
5. Run Script 
```bash 
python main.py
```

## Notes
The file `token.json` is automatically created during authentication.

Make sure your Google Cloud project has all APIs enabled:
* Google Sheets API
* Google Calendar API
* Google Drive API

Created by Humberto Bohorquez — built with Python and Google APIs.
