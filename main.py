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
import sql

DB_FILE = "schedule.db"
SCHEDULE_URL = "https://www.airblue.com/flightinfo/schedule"
IATA_LIST = scrapper.init_iata(DB_FILE, SCHEDULE_URL)
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
SCHEDULE_URL = "https://www.airblue.com/sched/schedule_popup.asp"
CHECK_SCHEDULE = sql.check_schedule(TRIP, DB_FILE, SCHEDULE_URL)
if len(CHECK_SCHEDULE[0]) == 0:
    print("No flights for " + str(TRIP[2]) + " and 2 next days")
    raise SystemExit(0)

URL = "https://www.airblue.com/bookings/flight_selection.aspx"
ROUND_TRIP = True
if len(TRIP) == 3:
    ROUND_TRIP = False

RESERVATION = scrapper.scrap(TRIP, CHECK_SCHEDULE, ROUND_TRIP, URL)
print("**********************")
print(RESERVATION[0])
for flight in RESERVATION[1]:
    print(flight)
