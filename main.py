"""
main module
input params in command line:
City depart
City destination
date of the direct flight
date of return flight (optional)
"""

import datetime
import itertools
import os
import sys

import operations
from timetable import TimeTable

DB_FILE = "schedule.db"
SCHEDULE_URL = "https://www.airblue.com/flightinfo/schedule"
IATA_LIST = operations.get_iata_from_url(SCHEDULE_URL)
if IATA_LIST is None:
    print("No connection to URL")
    raise SystemExit(1)
if not os.path.isfile(DB_FILE):
    operations.create_db(DB_FILE)
    operations.init_db(DB_FILE, IATA_LIST, 1)
else:
    CHECK_ALL_IATA_IN_DB = operations.check_all_iata_in_db(DB_FILE,
                                                           IATA_LIST)
    if CHECK_ALL_IATA_IN_DB == 1:
        print("Database was updated")
    elif CHECK_ALL_IATA_IN_DB != 0:
        print(CHECK_ALL_IATA_IN_DB)
        raise SystemExit(1)

INPUT_DATA = sys.argv
CHECK_INPUT_DATA = operations.check_input_data(INPUT_DATA, IATA_LIST)
if CHECK_INPUT_DATA != 0:
    print(CHECK_INPUT_DATA)
    raise SystemExit(1)

CHECK_DATES = operations.check_dates(INPUT_DATA)
if CHECK_DATES != 0:
    print(CHECK_DATES)
    raise SystemExit(1)

TRIP = INPUT_DATA[1:]
SCHEDULE_URL = "https://www.airblue.com/sched/schedule_popup.asp"
CHECK_SCHEDULE = operations.check_schedule(TRIP, DB_FILE, SCHEDULE_URL)
URL = "https://www.airblue.com/bookings/flight_selection.aspx"

if len(CHECK_SCHEDULE[0]) == 0:
    print("No flights for " + str(TRIP[2]) + " and 2 next days")
    raise SystemExit(0)
if len(TRIP) == 3:  # one way trip
    for DAY in CHECK_SCHEDULE[0]:
        DATE_FLIGHT = datetime.date(*list(map(int, TRIP[2].split('-')))) + \
                      datetime.timedelta(DAY)
        CURRENT_TRIP = TimeTable(TRIP[0], TRIP[1], str(DATE_FLIGHT))
        DATA_REQUEST = operations.create_data_request(CURRENT_TRIP)
        TREE_XML = operations.get_xml(URL, DATA_REQUEST)
        if TREE_XML is None:
            print("No connection to URL")
            raise SystemExit(1)
        FLIGHT_LIST = operations.parse_xml(CURRENT_TRIP, TREE_XML)
        if len(FLIGHT_LIST[0]) != 0:
            print(DATE_FLIGHT)
            for FLIGHT in FLIGHT_LIST[0]:
                print(FLIGHT)
        raise SystemExit(0)
# route trip
if len(CHECK_SCHEDULE[1]) == 0:
    print("You could by ticket from " + TRIP[0] + " to " +
          TRIP[1] + " for next days:")
    for DAY in CHECK_SCHEDULE[0]:
        DATE_FLIGHT = datetime.date(*list(map(int, TRIP[2].split('-')))) + \
                      datetime.timedelta(DAY)
        print(DATE_FLIGHT)
    print("But there are no flights back for " + TRIP[3] + " and 2 next days")
    raise SystemExit(0)

for DAY in CHECK_SCHEDULE[0]:
    for DAY_BACK in CHECK_SCHEDULE[1]:
        DATE_FLIGHT = datetime.date(*list(map(int, TRIP[2].split('-')))) + \
                      datetime.timedelta(DAY)
        DATE_FLIGHT_BACK = \
            datetime.date(*list(map(int, TRIP[3].split('-')))) + \
            datetime.timedelta(DAY_BACK)
        if DATE_FLIGHT > DATE_FLIGHT_BACK:
            continue
        CURRENT_TRIP = TimeTable(TRIP[0], TRIP[1], str(DATE_FLIGHT),
                                 str(DATE_FLIGHT_BACK))
        DATA_REQUEST = operations.create_data_request(CURRENT_TRIP)
        TREE_XML = operations.get_xml(URL, DATA_REQUEST)
        if TREE_XML is None:
            print("No connection to URL")
            raise SystemExit(1)
        FLIGHT_LIST = operations.parse_xml(CURRENT_TRIP, TREE_XML)
        if len(FLIGHT_LIST[0]) * len(FLIGHT_LIST[1]) > 0:
            FLIGHT_COMBINATION = list(map(list, itertools.product(
                FLIGHT_LIST[0], FLIGHT_LIST[1])))
            FLIGHT_COMBINATION = operations.check_return_flight(
                FLIGHT_COMBINATION, CURRENT_TRIP.date_1_trip,
                CURRENT_TRIP.date_2_trip)
            operations.add_total_price(FLIGHT_COMBINATION)
            FLIGHT_COMBINATION.sort(key=lambda x: x[2])
            if len(FLIGHT_COMBINATION) > 0:
                print("From " + TRIP[0] + " to " + TRIP[1] + " " +
                      str(DATE_FLIGHT))
                print("From " + TRIP[1] + " to " + TRIP[0] + " " +
                      str(DATE_FLIGHT_BACK))
                for FLIGHTS in FLIGHT_COMBINATION:
                    for FLIGHT in FLIGHTS:
                        print(FLIGHT)
                raise SystemExit(0)

print("No flights for your dates")
