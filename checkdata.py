"""
module of functions for checking input data and making some summary
"""

import datetime


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
    check_combination = []
    for flight_ in combination:
        if (len(args) > 1 and args[1] != args[2]) or \
                (time_sub(flight_[1].time_departure,
                          flight_[0].time_arrive) > 0
                 and (flight_[0].time_arrive[-2:] != "AM" or
                      flight_[0].time_departure[-2:] != "PM")):
            check_combination.append(flight_)
    return check_combination


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
