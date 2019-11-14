"""
main module
input params in command line:
City depart
City destination
date of the direct flight
date of return flight (optional)
"""
import sys

import checkdata
import scrapper
from scrapper import check_schedule

DB_FILE = "schedule.db"
IATA_LIST = scrapper.init_iata(DB_FILE)
if isinstance(IATA_LIST, str):
    print(IATA_LIST)
    raise SystemExit(1)

INPUT_DATA = sys.argv
CHECK_INPUT_DATA = checkdata.check_input_data(INPUT_DATA, IATA_LIST)
if CHECK_INPUT_DATA != 0:
    print(CHECK_INPUT_DATA)
    raise SystemExit(1)

CHECK_DATES = checkdata.check_dates(INPUT_DATA)
if CHECK_DATES != 0:
    print(CHECK_DATES)
    raise SystemExit(1)

TRIP = INPUT_DATA[1:]
CHECK_SCHEDULE = check_schedule(TRIP, DB_FILE)
if len(CHECK_SCHEDULE[0]) == 0:
    print("No flights for " + str(TRIP[2]) + " and 2 next days")
    raise SystemExit(0)

URL = "https://www.airblue.com/bookings/flight_selection.aspx"
ROUND_TRIP = True
if len(TRIP) == 3:
    ROUND_TRIP = False

RESERVATION = scrapper.scrap(TRIP, CHECK_SCHEDULE, ROUND_TRIP)
print("**********************")
print(RESERVATION[0])
for flight in RESERVATION[1]:
    print(flight)
