"""
module of function for database
"""

import datetime
import sqlite3

import parsing


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


def fill_schedule_db(url, trip, filename):
    """
    fill schedule database file
    :param url: schedule url
    :param trip: flight information (IATA1,IATA2,dates)
    :param filename: filename of database
    :return: 0 if is ok, None - if no flight in schedule
    """
    date_1_trip = datetime.date(*list(map(int, trip[2].split('-'))))
    schedule_data = xmlparspy.get_data_from_schedule(
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
    return 0


def schedule(iata1, iata2, filename):
    """
    get schedule information from database
    :param iata1: from iata
    :param iata2: dest iata
    :param filename: database filename
    :return: string contained +/- : in schedule/not in schedule
    """
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    sql = "SELECT * FROM flight WHERE (DEPART_IATA = ? AND ARRIVE_IATA = ?)"
    cursor.execute(sql, (iata1, iata2))
    data_row = cursor.fetchall()
    conn.close()
    return data_row


def check_schedule(trip, filename, url):
    """
    check trip in schedule
    if schedule doesn't contain information => fill schedule from url
    :param trip: flight information (IATA1,IATA2,dates)
    :param filename: filename of database
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
        if fill_schedule_db(url, trip, filename) is None:
            return None

    data_row1 = schedule(trip[0], trip[1], filename)
    data_row2 = schedule(trip[1], trip[0], filename)
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
