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

0. in case of invalid data:

0.1. in case of quantity of args not 3 and not 4:

"waiting for 3 or 4 arguments but given ..."

0.2. in case of wrong IATA1 or IATA2:
"... not in IATA_LIST"
0.3. in case of wrong date(s) format:
"Dates isn't correct. Use format YYYY-MM-DD"
0.4. in case of date2<date1:
"Date of depart should be at future time"
1. in case of one way trip (date2 is absent):
1.1. in case of there are no fligths in schedule for date1 and two next days:
"No flights for _date1_ and 2 next days"
1.2. in case of there are no tickets for for date1 and two next days:
"No tickets for your dates"
