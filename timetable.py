"""
class Timetable
"""


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
