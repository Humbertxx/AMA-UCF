from .AMAgoogleSheets import retrievingKeyGspread, autoUpdate, normalizingEvents, getAllWorksheet
from .AMAgoogleCalendar import retrieveKeyGCalendar, createEvent, create_new_calendar


from flask import Flask
from AMAflex import AMAapp

from ProcessCalendar import sync_events

app = Flask(__name__)
app.config['SECRET_KEY'] = 'API_KEY HERE'
