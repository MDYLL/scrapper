# scrapper
program is looking for tickets by parsing https://www.airblue.com/

input format:

python.exe main.py IATA1 IATA2 date1 [date2]

IATA1 - iata code of the first airport

IATA2 - iata code of the second airport

date1 - wish date of the fligth from the first airport to to the second

date2 - wish date of the flight from the second airport to the first

format of dates is YYYY-MM-DD

output data (console):


0. in case of invalid data or some problems with url or database connetction:

0.1. in case of quantity of args not 3 and not 4:

"waiting for 3 or 4 arguments but given ..."

0.2. in case of wrong IATA1 or IATA2:

"... not in IATA_LIST"

0.3. in case of wrong date(s) format:

"Dates isn't correct. Use format YYYY-MM-DD"

0.4. in case of date2<date1:

"Date of depart should be at future time"

0.5. in case of problem with url connection:

"No connection to URL"

0.6. in case of problem with database file:

"Bad DB file"

1. in case of one way trip (date2 is absent):

1.1. in case of there are no fligths in schedule for date1 and two next days:

"No flights for _date1_ and 2 next days"

1.2. else in case of there are no tickets for date1 and two next days:

"No tickets for your dates"

1.3. else list of flights for nearest date sorted by price in format:

**********************

From _IATA1_ to _IATA2_ _nearest date_

FROM: _IATA1_ DESTINATION: _IATA2_ DEPART: _time_d_ ARRIVE : _time_a_ TIME FLIGHT: _time_f_ CLASS: _class_ PRICE: _price_

TOTAL: _price_

**********************

where:

time_d - departure time

time_a - arrive time

time_f - flight time

class - class

price - price in format 'USD 9,999'

strings 2 and 3 for each flight in list

2. in case of round trip (date2 is present):

2.1.in case of there are no fligths from IATA1 to IATA2 in schedule for date1 and two next days:

"No flights for _date1_ and 2 next days"

2.2. else in case of there are no flights from IATA2 to IATA1 for for date2 and two next days:

**********************

"You could by ticket from _IATA1_ to _IATA2_ for next days:

_list of dates_

But there are no flights back for _date2_ and 2 next days

**********************

where list of dates - list of possible dates flights from IATA1 to IATA2

2.3. else in case of there are no tickets for round trip for date1 (+2 days) and date 2 (+ 2 days):

"No tickets for your dates"

2.4. else list of tuples fligths from IATA1 to IATA2 and from IATA2 to IATA1 for dates nearest to date1 and date2 sorted by total price in format:

**********************

From _IATA1_ to _IATA2_ _nearest date1_

From _IATA2_ to _IATA1_ _nearest date2_

FROM: _IATA1_ DESTINATION: _IATA2_ DEPART: _time_d1_ ARRIVE : _time_a1_ TIME FLIGHT: _time_f1_ CLASS: _class1_ PRICE: _price1_

FROM: _IATA2_ DESTINATION: _IATA1_ DEPART: _time_d2_ ARRIVE : _time_a2_ TIME FLIGHT: _time_f2_ CLASS: _class_ PRICE: _price2_

TOTAL: _price_t_

**********************

where:

time_d(1,2) - departure time

time_a(1,2) - arrive time

time_f(1,2) - flight time

class(1,2) - class

price(1,2,t) - price in format 'USD 9,999'

price_t=price1+price2

strings 3,4,5 for each tuple in list
