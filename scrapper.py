"""
main functions for scrapping
"""

import datetime
import itertools
import os

import operations
from timetable import TimeTable


def init_iata(db_file, schedule_url):
    """
    initialization of IATA list
    :param db_file: IATA database filename
    :param schedule_url: schedule url for parsing
    :return: IATA list
    """
    iata_list = operations.get_iata_from_url(schedule_url)
    if iata_list is None:
        return "No connection to URL"
    if not os.path.isfile(db_file):
        operations.create_db(db_file)
        operations.init_db(db_file, iata_list, 1)
    else:
        check_all_data_in_db = operations.check_all_iata_in_db(db_file,
                                                               iata_list)
        if check_all_data_in_db == 1:
            print("Database was updated")
        elif check_all_data_in_db != 0:
            return check_all_data_in_db
    return iata_list


def scrap(trip, schedule, round_trip, url):
    """
    scrapping URL and return result (possible flights)
    :param trip: trip information
    :param schedule:
    :param round_trip: true if round else false
    :param url: url for parsing tickets
    :return: reservation - message and list of the flights
    """
    reservations = list()
    reservations.append("message")
    reservations.append(list())
    if not round_trip:  # one way trip
        for day in schedule[0]:
            date_flight = datetime.date(
                *list(map(int, trip[2].split('-')))) + datetime.timedelta(day)
            current_trip = TimeTable(trip[0], trip[1], str(date_flight))
            data_request = operations.create_data_request(current_trip)
            tree_xml = operations.get_xml(url, data_request)
            if tree_xml is None:
                reservations[0] = "No connection to URL"
                return reservations
            flight_list = operations.parse_xml(current_trip, tree_xml)
            if len(flight_list[0]) != 0:
                reservations[0] = date_flight
                for flight in flight_list[0]:
                    reservations[1].append(flight)
            return reservations
    # round trip
    if len(schedule[1]) == 0:
        reservations[0] = "You could by ticket from " + trip[0] + " to " + \
                          trip[1] + " for next days:"
        for day in schedule[0]:
            date_flight = datetime.date(
                *list(map(int, trip[2].split('-')))) + datetime.timedelta(day)
            reservations[0] += "\n"
            reservations[0] += date_flight
        reservations[0] += "But there are no flights back for " \
                           + trip[3] + " and 2 next days"
        return reservations

    for day in schedule[0]:
        for day_back in schedule[1]:
            date_flight = datetime.date(
                *list(map(int, trip[2].split('-')))) + datetime.timedelta(day)
            date_flight_back = datetime.date(
                *list(map(int, trip[3].split('-')))) + \
                               datetime.timedelta(day_back)
            if date_flight > date_flight_back:
                continue
            current_trip = TimeTable(trip[0], trip[1], str(date_flight),
                                     str(date_flight_back))
            data_request = operations.create_data_request(current_trip)
            tree_xml = operations.get_xml(url, data_request)
            if tree_xml is None:
                reservations[0] = "No connection to URL"
                return reservations
            flight_list = operations.parse_xml(current_trip, tree_xml)
            if len(flight_list[0]) * len(flight_list[1]) > 0:
                flight_combination = list(map(list, itertools.product(
                    flight_list[0], flight_list[1])))
                flight_combination = operations.check_return_flight(
                    flight_combination, current_trip.date_1_trip,
                    current_trip.date_2_trip)
                operations.add_total_price(flight_combination)
                flight_combination.sort(key=lambda x: x[2])
                if len(flight_combination) > 0:
                    reservations[0] = "From " + trip[0] + " to " + trip[1] \
                                      + " " + str(date_flight)
                    reservations[0] += "\n"
                    reservations[0] += "From " + trip[0] + " to " + trip[1] \
                                       + " " + str(date_flight)
                    for flights in flight_combination:
                        for flight in flights:
                            reservations[1].append(flight)
                    return reservations

    reservations[0] = "No flights for your dates"
    return reservations
