"""
module of functions
"""

import datetime
import re
import sqlite3
from io import StringIO

import requests
import urllib3
from lxml import etree

from flight import Flight


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
    :return: etree object
    """
    header = {'Accept-Encoding': 'identity'}
    try:
        response = requests.get(url, stream=True,
                                params=data_request, headers=header)
    except requests.exceptions.RequestException:
        return None
    parser = etree.HTMLParser()
    tree_xml = etree.parse(StringIO(response.content.decode("utf-8")), parser)
    return tree_xml


def parse_xml(trip, tree_xml):
    """
    parsing etree object
    :param trip: TimeTable
    :param tree_xml: etree object
    :return: tuple of list of direct flights and list of back flights
    """
    flight_1_trip = list()
    index_1_trip = 2
    while True:
        try:
            to_direction = tree_xml.getroot()[1][4][0][2][2][7][index_1_trip]
        except IndexError:
            break
        td_dep = to_direction[0][1]
        td_arr = to_direction[0][3]
        index_1_trip_class = 5
        while True:
            try:
                td_class = to_direction[0][index_1_trip_class]
            except IndexError:
                break
            td_cost = td_class[0]
            flight_1_trip.append(
                Flight(trip.city_departure, trip.city_arrive, td_dep.text,
                       td_arr.text, td_class.attrib['class'],
                       td_cost.attrib['data-title'].split('\n')[1]))
            index_1_trip_class += 1
        index_1_trip += 1
    flight_2_trip = list()
    if not trip.date_2_trip:
        return tuple((flight_1_trip, flight_2_trip))
    index_2_trip = 2
    while True:
        try:
            to_direction = tree_xml.getroot()[1][4][0][2][3][7][index_2_trip]
        except IndexError:
            break
        td_dep = to_direction[0][1]
        td_arr = to_direction[0][3]
        index_2_trip_class = 5
        while True:
            try:
                td_class = to_direction[0][index_2_trip_class]
            except IndexError:
                break
            td_cost = td_class[0]
            flight_2_trip.append(
                Flight(trip.city_arrive, trip.city_departure, td_dep.text,
                       td_arr.text, td_class.attrib['class'],
                       td_cost.attrib['data-title'].split('\n')[1]))
            index_2_trip_class += 1
        index_2_trip += 1
    return tuple((flight_1_trip, flight_2_trip))


def add_total_price(combination):
    """
    adding flight total cost to each combination of the
    flights (in case we have back flight) or adding cost to list of one flight
    :param combination: combination of direct and back flights
    :return: list of flights wiht total cost
    """
    for flight_ in combination:
        total_price = 0
        each = None
        for each in flight_:
            if ',' in each.price[4:]:
                total_price += int(float(
                    each.price[4:].replace(',', '.')) * 1000)
            else:
                total_price += int(each.price[4:])
        flight_.append("Total :" + each.price[0:3] + " " + str(total_price))


def time_sub(str_time1, str_time2):
    """
    count substract time1-time2
    :param str_time1: string of time in format 00:00 AM
    :param str_time2:  string of time in format 00:00 AM
    :return: subtracts in minutes
    """
    time_day_1, part_day_1 = str_time1.split(' ')
    time_day_1_hours, time_day_1_minutes = time_day_1.split(':')
    if part_day_1 == 'PM' and time_day_1_hours != "12":
        time1 = 12 * 60
    else:
        time1 = 0
    time1 += int(time_day_1_hours) * 60 + int(time_day_1_minutes)

    time_day_2, part_day_2 = str_time2.split(' ')
    time_day_2_hours, time_day_2_minutes = time_day_2.split(':')
    if part_day_2 == 'PM' and time_day_2_hours != "12":
        time2 = 12 * 60
    else:
        time2 = 0
    time2 += int(time_day_2_hours) * 60 + int(time_day_2_minutes)
    return time1 - time2


def check_return_flight(*args):
    """
    check pair of flights for opportunities get back flight
    :param args: combination of direct and back flights
    :return: combination without impossible connection
    """
    combination = args[0]
    check_combination = list()
    for flight_ in combination:
        if (len(args) > 1 and args[1] != args[2]) or \
                (time_sub(flight_[1].time_departure,
                          flight_[0].time_arrive) > 0
                 and (flight_[0].time_arrive[-2:] != "AM" or
                      flight_[0].time_departure[-2:] != "PM")):
            check_combination.append(flight_)
    return check_combination


def get_iata_from_url(schedule_url):
    """
    create list of IATA from url
    :param schedule_url: url for getting schedule
    :return: list of IATA
    """
    tree_xml = get_xml(schedule_url, None)
    if tree_xml is None:
        return None
    iata_list = list()
    root = tree_xml.getroot()[1][0][0][1][0][0][0][5][0]
    string_index = 0
    while True:
        try:
            data = root[string_index].tail
        except IndexError:
            break
        for each in re.split(' |,', data):
            if len(each) > 0 and each[0] == '(':
                iata_list.append(each[1:4])
        string_index += 1
    return iata_list


def create_db(filename):
    """
    create database for schedule
    :param filename: file with database
    :return: nothing
    """
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE flight
    (Route_ID int,
    DEPART_IATA text,
    ARRIVE_IATA text,
    SCHEDULE text)
    """)
    conn.commit()
    conn.close()


def init_db(filename, iata_list, prim_key):
    """
    init database with empty information for each possible flight
    :param filename: file with database
    :param iata_list: iata list
    :param pk: primary_key, index of first row's ID
    :return: nothing
    """
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    primary_key = prim_key
    for depart in iata_list:
        for arrive in iata_list:
            if depart != arrive:
                sql = "SELECT * FROM flight " \
                      "WHERE DEPART_IATA=? AND ARRIVE_IATA=?"
                cursor.execute(sql, [depart, arrive])
                if len(cursor.fetchall()) == 0:
                    cursor.execute("INSERT INTO flight VALUES (?,?,?,?)",
                                   (primary_key, depart, arrive, '0000000'))
                    conn.commit()
                    primary_key += 1
    conn.close()


def check_input_data(input_data, iata_list):
    """
    check input data for quantity and IATA's validation
    :param input_data: arguments from command line
    :param iata_list: IATA list
    :return: 0 if ok, error message if not
    """
    if len(input_data) < 4 or len(input_data) > 5:
        return "waiting for 3 or 4 arguments but given " + \
               str(len(input_data) - 1)
    if input_data[1] not in iata_list:
        return input_data[1] + " not in IATA_LIST"
    if input_data[2] not in iata_list:
        return input_data[2] + " not in IATA_LIST"
    return 0


def check_dates(input_data):
    """
    check dates for validation:
    1. they are in valid format
    2. first date is today or later
    3. second date equal first date or later
    :param input_data: arguments from command line
    :return: 0 if ok, error message if not
    """
    try:
        date_1_trip = datetime.date(*list(map(int, input_data[3].split('-'))))
        date_2_trip = date_1_trip
        if len(input_data) > 4:
            date_2_trip = datetime.date(
                *list(map(int, input_data[4].split('-'))))
    except TypeError:
        return "Dates isn't correct. Use format YYYY-MM-DD"
    if date_1_trip < datetime.date.today():
        return "Date of depart should be at future time"
    if date_1_trip > date_2_trip:
        return "Date of arrive should be same or later of date of depart"
    return 0


def check_all_iata_in_db(filename, iata_list):
    """
    check that all current IATAs in database
    :param filename: file name of database
    :param iata_list: current IATA list
    :return: 0 if all IATAs in database,
    1 - if database was updated, message error in case of problem with DB
    """
    try:
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        sql = "SELECT * FROM flight"
        cursor.execute(sql)
    except sqlite3.OperationalError:
        return "Bad DB file"
    lines_in_db = len(cursor.fetchall())
    conn.close()
    if len(iata_list) * (len(iata_list) - 1) == lines_in_db:
        return 0
    init_db(filename, iata_list, lines_in_db + 1)
    return 1


def get_data_from_schedule(url, iata1, iata2, date_trip):
    """
    get information about flights from schedule
    :param date_trip: date of the flight
    :param url: url with schedule
    :param iata1: depart city
    :param iata2: destination city
    :return: tuple of strings with possible days
    for flight in format "++---++" or None in case error
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
        response = requests.post(url, data=data_request, verify=False)
    except requests.exceptions.RequestException:
        return None
    parser = etree.HTMLParser()
    tree_xml = etree.parse(StringIO(response.content.decode("utf-8")), parser)
    dates_1_trip = '-------'
    dates_2_trip = '-------'
    flight_index = 1
    while True:
        try:
            first_flight = tree_xml.getroot()[1][0][0][0][1][2][0][0][0][1][0][0][flight_index]
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


def check_schedule(trip, filename, url):
    """
    check trip in schedule
    if schedule doesn't contain information => fill schedule from url
    :param trip: flight information (IATA1,IATA2,dates)
    :param filename: file name of database
    :param url: schedule url
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
        schedule_data = get_data_from_schedule(
            url, trip[0], trip[1], date_1_trip)
        if schedule_data is None:
            return None
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        cursor.execute("""UPDATE flight SET SCHEDULE = ?
        WHERE (DEPART_IATA = ? AND ARRIVE_IATA = ?)""",
                       (schedule_data[0], trip[0], trip[1]))
        conn.commit()
        cursor.execute("""UPDATE flight SET SCHEDULE = ?
        WHERE (DEPART_IATA = ? AND ARRIVE_IATA = ?)""",
                       (schedule_data[1], trip[1], trip[0]))
        conn.commit()
        conn.close()
    conn1 = sqlite3.connect(filename)
    cursor1 = conn1.cursor()
    sql1 = "SELECT * FROM flight WHERE (DEPART_IATA = ? AND ARRIVE_IATA = ?)"
    cursor1.execute(sql1, (trip[0], trip[1]))
    data_row1 = cursor1.fetchall()
    conn1.close()
    conn2 = sqlite3.connect(filename)
    cursor2 = conn2.cursor()
    sql2 = "SELECT * FROM flight WHERE (DEPART_IATA = ? AND ARRIVE_IATA = ?)"
    cursor2.execute(sql2, (trip[1], trip[0]))
    data_row2 = cursor2.fetchall()
    conn2.close()
    date_1_trip_weekday = date_1_trip.weekday()  # monday is 0
    if date_2_trip is not None:
        date_2_trip_weekday = date_2_trip.weekday()  # monday is 0
    else:
        date_2_trip_weekday = None
    flight_possible = list()
    flight_possible.append(list())
    flight_possible.append(list())
    for i in range(3):
        if data_row1[0][3][(date_1_trip_weekday + i) % 7] == '+':
            flight_possible[0].append(i)
        if date_2_trip is not None and \
                data_row2[0][3][(date_2_trip_weekday + i) % 7] == '+':
            flight_possible[1].append(i)

    return flight_possible
