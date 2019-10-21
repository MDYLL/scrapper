"""
class Flight
"""

import operations


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
        time_flight = operations.time_sub(self.time_arrive,
                                          self.time_departure)
        while time_flight < 0:
            time_flight += 12 * 60
        return "FROM: %s DESTINATION: %s DEPART: %s ARRIVE: %s " \
               "TIME FLIGHT: %s CLASS: %s PRICE: %s" % \
               (self.city_departure, self.city_destination,
                self.time_departure, self.time_arrive, str(time_flight // 60) +
                ':' + str(time_flight % 60), self.service_class, self.price)
