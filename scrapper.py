"""
main functions for scrapping
"""

import datetime
import itertools
import os
import re
import sqlite3

import requests
import urllib3
from lxml import html

import checkdata
from db import Flight
from db import TimeTable
from db import init_db, create_db, check_all_iata_in_db, \
    schedule, put_data_in_db

SCHEDULE_URL = "https://www.airblue.com/flightinfo/schedule"
SCHEDULE_URL_POPUP = "https://www.airblue.com/sched/schedule_popup.asp"
URL = "https://www.airblue.com/bookings/flight_selection.aspx"


def create_data_request(trip):
    """
    creating data of flights
    :param trip: TimeTable
    :return: dict for HTTP-request
    """
    data_request = dict()
    data_request.update(
        {'DC': trip.city_departure, 'AC': trip.city_arrive,
         'AM': trip.date_1_trip[:7], 'AD': trip.date_1_trip[-2:],
         'PA': 1, 'FL': 'on', 'x': 49, 'y': 12})
    if trip.date_2_trip:
        data_request.update({'TT': 'RT', 'RM': trip.date_2_trip[:7],
                             'RD': trip.date_2_trip[-2:]})
    return data_request


def get_xml(url, data_request):
    """
    creating etree object
    :param url: url for request
    :param data_request: dict of data
    :return: html-content
    """
    header = {'Accept-Encoding': 'identity'}
    try:
        response = requests.get(url, stream=True,
                                params=data_request, headers=header)
    except requests.exceptions.RequestException:
        return None
    return response.content


def parse_flight(trip, content, flight_index):
    """
    parsing etree object
    :param flight_index: 0/1 - direct/back
    :param trip: TimeTable
    :param content: etree object
    :return: list of flights
    """
    flight_trip = []
    index_trip = 2
    while True:
        try:
            root = html.fromstring(content)
            to_direction = root.xpath(
                '//table[contains(@class,"flight_selection") '
                'and contains(@class, "current-date")]')[flight_index][index_trip]
            td_dep = to_direction[0][1]
            td_arr = to_direction[0][3]
        except IndexError:
            break
        index_trip_class = 5
        while True:
            try:
                td_class = to_direction[0][index_trip_class]
            except IndexError:
                break
            td_cost = td_class[0]
            if flight_index == 0:
                flight_trip.append(
                    Flight(trip.city_departure, trip.city_arrive, td_dep.text,
                           td_arr.text, td_class.attrib['class'],
                           td_cost.attrib['data-title'].split('\n')[1]))
            else:
                flight_trip.append(
                    Flight(trip.city_arrive, trip.city_departure, td_dep.text,
                           td_arr.text, td_class.attrib['class'],
                           td_cost.attrib['data-title'].split('\n')[1]))
            index_trip_class += 1
        index_trip += 1
    return flight_trip


def parse_xml(trip, content):
    """
    parsing etree object
    :param trip: TimeTable
    :param content: etree object
    :return: tuple of list of direct flights and list of back flights
    """
    flight_1_trip = parse_flight(trip, content, 0)
    flight_2_trip = []
    if not trip.date_2_trip:
        return tuple((flight_1_trip, flight_2_trip))
    flight_2_trip = parse_flight(trip, content, 1)
    return tuple((flight_1_trip, flight_2_trip))


def get_iata_from_url():
    """
    :return: list of IATA
    """
    content = get_xml(SCHEDULE_URL, None)
    if content is None:
        return None
    iata_list = []
    tree = html.fromstring(content)
    tag = tree.xpath('//div[@align="center"]')
    string_index = 0
    while True:
        try:
            data = tag[0][0][string_index].tail
        except IndexError:
            break
        for each in re.split(' |,', data):
            if len(each) > 0 and each[0] == '(':
                iata_list.append(each[1:4])
        string_index += 1
    return iata_list


def get_schedule_from_url(iata1, iata2, date_trip):
    """
    get response about flights
    :param date_trip: date of the flight
    :param iata1: depart city
    :param iata2: destination city
    :return: response
    """
    urllib3.disable_warnings()
    nearest_monday = (date_trip + datetime.timedelta(
        days=-date_trip.weekday(), weeks=1)).strftime('%Y-%m-%d')
    data_request = {
        'profiles_action': 'update',
        'market_id': '',
        'origin': iata1,
        'destination': iata2,
        'start_week': nearest_monday}
    try:
        response = requests.post(SCHEDULE_URL_POPUP,
                                 data=data_request, verify=False)
    except requests.exceptions.RequestException:
        return None
    return response


def get_data_from_schedule(iata1, iata2, date_trip):
    """
    get information about flights from schedule
    :param date_trip: date of the flight
    :param url: url with schedule
    :param iata1: depart city
    :param iata2: destination city
    :return: tuple of strings with possible days
    for flight in format "++---++" or None in case error
    """
    response = get_schedule_from_url(iata1, iata2, date_trip)
    if response is None:
        return None
    dates_1_trip = '-------'
    dates_2_trip = '-------'
    root = html.fromstring(response.content).xpath('//tr[@align="center"]')
    flight_index = 1
    while True:
        try:
            first_flight = root[flight_index]
        except IndexError:
            break
        for i in range(7):
            flight_info = first_flight[i + 2].text
            if flight_info != '---':
                if first_flight.attrib['id'][-3:] == iata2:
                    dates_1_trip = dates_1_trip[:i] + '+' + \
                                   dates_1_trip[i + 1:]
                else:
                    dates_2_trip = dates_2_trip[:i] + '+' + \
                                   dates_2_trip[i + 1:]
        flight_index += 1
    return tuple((dates_1_trip, dates_2_trip))


def fill_schedule_db(trip, filename):
    """
    fill schedule database file
    :param trip: flight information (IATA1,IATA2,dates)
    :param filename: filename of database
    :return: 0 if is ok, None - if no flight in schedule
    """
    date_1_trip = datetime.date(*list(map(int, trip[2].split('-'))))
    schedule_data = get_data_from_schedule(trip[0], trip[1], date_1_trip)
    if schedule_data is None:
        return None
    put_data_in_db(schedule_data, trip, filename)
    return 0


def check_schedule(trip, filename):
    """
    check trip in schedule
    if schedule doesn't contain information => fill schedule from schedule_url
    :param trip: flight information (IATA1,IATA2,dates)
    :param filename: filename of database
    :return: tuple(list()) - possible dates for flight.
    0 - exact, 1/2 - plus 1/2 day(s)
    """
    date_1_trip = datetime.date(*list(map(int, trip[2].split('-'))))
    date_2_trip = None
    if len(trip) > 3:
        date_2_trip = datetime.date(*list(map(int, trip[3].split('-'))))
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    sql = "SELECT * FROM flight WHERE (DEPART_IATA = ? AND ARRIVE_IATA = ?)"
    cursor.execute(sql, (trip[0], trip[1]))
    data_row = cursor.fetchall()
    conn.close()
    if data_row[0][3] == "0000000":
        if fill_schedule_db(trip, filename) is None:
            return None

    data_row1 = schedule(trip[0], trip[1], filename)
    data_row2 = schedule(trip[1], trip[0], filename)
    date_1_trip_weekday = date_1_trip.weekday()  # monday is 0
    if date_2_trip is not None:
        date_2_trip_weekday = date_2_trip.weekday()  # monday is 0
    else:
        date_2_trip_weekday = None
    flight_possible = []
    flight_possible.append([])
    flight_possible.append([])
    for i in range(3):
        if data_row1[0][3][(date_1_trip_weekday + i) % 7] == '+':
            flight_possible[0].append(i)
        if date_2_trip is not None and \
                data_row2[0][3][(date_2_trip_weekday + i) % 7] == '+':
            flight_possible[1].append(i)

    return flight_possible


def init_iata(db_file):
    """
    initialization of IATA list
    :param db_file: IATA database filename
    :return: IATA list
    """
    iata_list = get_iata_from_url()
    if iata_list is None:
        return "No connection to URL"
    if not os.path.isfile(db_file):
        create_db(db_file)
        init_db(db_file, iata_list, 1)
    else:
        check_all_data_in_db = check_all_iata_in_db(db_file,
                                                    iata_list)
        if check_all_data_in_db == 1:
            print("Database was updated")
        elif check_all_data_in_db != 0:
            return check_all_data_in_db
    return iata_list


def scrap(trip, checked_schedule, round_trip):
    """
    scrapping URL and return result (possible flights)
    :param trip: trip information
    :param checked_schedule: tuple(list()) - possible dates for flight.
    0 - exact, 1/2 - plus 1/2 day(s)
    :param round_trip: true if round else false
    :return: reservation - message and list of the flights
    """
    reservations = []
    reservations.append("")
    reservations.append([])
    if len(checked_schedule[1]) == 0 and round_trip:
        reservations[0] = "You could by ticket from " + trip[0] + " to " + \
                          trip[1] + " for next days:"
        for day in checked_schedule[0]:
            date_flight = datetime.date(
                *list(map(int, trip[2].split('-')))) + datetime.timedelta(day)
            reservations[0] += "\n"
            reservations[0] += str(date_flight) + "\n"
        reservations[0] += "But there are no flights back for " \
                           + trip[3] + " and 2 next days"
        return reservations
    if len(checked_schedule[1]) == 0 and not round_trip:
        checked_schedule[1].append(None)

    for day in checked_schedule[0]:
        for day_back in checked_schedule[1]:
            if day != 0 or day_back != 0:
                reservations[0] = 'No tickets on your dates\n' + reservations[0]
            date_flight = datetime.date(
                *list(map(int, trip[2].split('-')))) + datetime.timedelta(day)
            if round_trip:
                date_flight_back = datetime.date(
                    *list(map(int, trip[3].split('-')))) + \
                                   datetime.timedelta(day_back)
                if date_flight > date_flight_back:
                    continue
                current_trip = TimeTable(trip[0], trip[1], str(date_flight),
                                         str(date_flight_back))
            else:
                current_trip = TimeTable(trip[0], trip[1], str(date_flight))
            data_request = create_data_request(current_trip)
            tree_xml = get_xml(URL, data_request)
            if tree_xml is None:
                reservations[0] = "No connection to URL"
                return reservations
            flight_list = parse_xml(current_trip, tree_xml)
            if len(flight_list[0]) != 0 and not round_trip:
                reservations[0] += str(date_flight)
                for flight in flight_list[0]:
                    reservations[1].append(flight)
                return reservations
            if len(flight_list[0]) * len(flight_list[1]) > 0:
                flight_combination = list(map(list, itertools.product(
                    flight_list[0], flight_list[1])))
                flight_combination = checkdata.check_return_flight(
                    flight_combination, current_trip.date_1_trip,
                    current_trip.date_2_trip)
                checkdata.add_total_price(flight_combination)
                flight_combination.sort(key=lambda x: x[2])
                if len(flight_combination) > 0:
                    reservations[0] += "From " + trip[0] + " to " + trip[1] \
                                       + " " + str(date_flight)
                    reservations[0] += "\n"
                    reservations[0] += "From " + trip[1] + " to " + trip[0] \
                                       + " " + str(date_flight_back)
                    for flights in flight_combination:
                        for flight in flights:
                            reservations[1].append(flight)
                    return reservations

    reservations[0] = "No tickets for your dates"
    return reservations
