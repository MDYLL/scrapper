"""
module of function for parsing
"""

import datetime
import re

import requests
import urllib3
from lxml import html

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
    flight_trip = list()
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
            flight_trip.append(
                Flight(trip.city_departure, trip.city_arrive, td_dep.text,
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
    flight_2_trip = list()
    if not trip.date_2_trip:
        return tuple((flight_1_trip, flight_2_trip))
    flight_2_trip = parse_flight(trip, content, 1)
    return tuple((flight_1_trip, flight_2_trip))


def get_iata_from_url(schedule_url):
    """
    create list of IATA from url
    :param schedule_url: url for getting schedule
    :return: list of IATA
    """
    content = get_xml(schedule_url, None)
    if content is None:
        return None
    iata_list = list()
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


def get_schedule_from_url(url, iata1, iata2, date_trip):
    """
    get response about flights from url
    :param date_trip: date of the flight
    :param url: url with schedule
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
        response = requests.post(url, data=data_request, verify=False)
    except requests.exceptions.RequestException:
        return None
    return response


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
    response = get_schedule_from_url(url, iata1, iata2, date_trip)
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
