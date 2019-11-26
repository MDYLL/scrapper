"""
module of function for database
"""

import sqlite3

import checkdata


class TimeTable:
    """
    initialization
    """

    def __init__(self, *args):
        self.city_departure = args[0]
        self.city_arrive = args[1]
        self.date_1_trip = args[2]
        if len(args) == 4:
            self.date_2_trip = args[3]
        else:
            self.date_2_trip = 0


class Flight:
    """
    class initialization and representative
    """

    def __init__(self, city_departure, city_destination, time_departure,
                 time_arrive, service_class, price):
        self.city_departure = city_departure
        self.city_destination = city_destination
        self.time_departure = time_departure
        self.time_arrive = time_arrive
        self.service_class = service_class
        self.price = price

    def __repr__(self):
        time_flight = checkdata.time_sub(self.time_arrive,
                                         self.time_departure)
        while time_flight < 0:
            time_flight += 12 * 60
        return "FROM: %s DESTINATION: %s DEPART: %s ARRIVE: %s " \
               "TIME FLIGHT: %s CLASS: %s PRICE: %s" % \
               (self.city_departure, self.city_destination,
                self.time_departure, self.time_arrive, str(time_flight // 60) +
                ':' + str(time_flight % 60), self.service_class, self.price)


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
    :param prim_key: primary_key, index of first row's ID
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
    except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
        return "Bad DB file"
    lines_in_db = len(cursor.fetchall())
    conn.close()
    if len(iata_list) * (len(iata_list) - 1) == lines_in_db:
        return 0
    init_db(filename, iata_list, lines_in_db + 1)
    return 1


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


def put_data_in_db(schedule_data, trip, filename):
    """
    fill db
    :param schedule_data: tuple of strings with possible days
    for flight in format "++---++"
    :param trip: flight information (IATA1,IATA2,dates)
    :param filename: filename of database
    :return:
    """
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
