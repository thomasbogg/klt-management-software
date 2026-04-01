import datetime

from default.booking.booking import Booking
from default.booking.functions import logbooking
from default.dates import dates
from default.update.wrapper import update
from default.database.functions import search_valid_bookings, get_property_price
from utils import log, superlog


@update
def check_price_divergences(start: datetime.date, end: datetime.date):
    """
    Check for price divergences in the database.

    Parameters:
        start: The start date for the bookings.
        end: The end date for the bookings.

    Returns:
        None: This function does not return anything.
    """
    bookings = get_valid_bookings(start=start, end=end)
    undercharged = list()
    propertiesPercentages = dict()

    for booking in bookings:
        priceId = booking.property.priceId
        nightsByMonth = get_total_nights_by_month(booking)
        year = booking.arrival.date.year
        #departureYear = booking.departure.date.year
            
        standardCharge = calculate_standard_charge_for_booking(priceId, year, nightsByMonth)
        difference = booking.charges.basicRental / standardCharge
        
        if difference < .9:
            booking.underchargedFactor = difference
            undercharged.append(booking)

        if booking.property.name not in propertiesPercentages:
            propertiesPercentages[booking.property.name] = list()

        propertiesPercentages[booking.property.name].append((difference, booking.totalNights))

    log_results(propertiesPercentages, undercharged)
    return 'All prices charged checked for given period!'
    

def log_results(propertiesPercentages: dict, undercharged: list):
    """
    Log the results of the price divergence check.
    Parameters:
        propertiesPercentages: A dictionary with property names and their price differences.
        undercharged: A list of bookings that are undercharged.
    """
    if undercharged:
        log('The following bookings are undercharged:')
        for booking in undercharged:
            logbooking(booking, inline=f'By a Factor of {booking.underchargedFactor:.2f}')

    superlog('This is the average price divergence for each property with bookings checked for the given period:')
    for propertyName, percentagesNights in propertiesPercentages.items():
        if len(percentagesNights) > 1:
            averagePrice = sum(price for price, _ in percentagesNights) / len(percentagesNights)
            averageNights = sum(nights for _, nights in percentagesNights) / len(percentagesNights)
            log(f'{propertyName} has an average price difference of {averagePrice:.2f} for {averageNights:.2f} nights.')
            
            
def calculate_standard_charge_for_booking(priceId: str, year: int, nightsByMonth: dict[str, int]) -> float:
    """
    Calculate the standard charge for a booking based on nights per month.
    
    Parameters:
        nightsByMonth: A dictionary with months as keys and number of nights as values.
        
    Returns:
        float: The total standard charge for the booking.
    """
    total = 0
    for month, nights in nightsByMonth.items(): 
        prices = get_property_price(name=priceId, month=month, year=year).fetchone()
        perNight = getattr(prices, month) / 7
        total += nights * perNight
    return total


def get_total_nights_by_month(booking: Booking) -> dict[str, int]:
    """
    Get total nights broken by month of a booking.
    
    Parameters:
        booking: The booking object.
        
    Returns:
        dict: A dict of months and days in the booking.
    """
    monthsDays = dict()
    startMonth = booking.arrival.date.month
    endMonth = booking.departure.date.month

    if startMonth == endMonth:
        stringMonth = dates.stringMonths()[startMonth - 1].lower()
        monthsDays[stringMonth] = dates.subtractDates(booking.departure.date, booking.arrival.date)
        return monthsDays
    
    for month in range(startMonth, endMonth + 1):
        stringMonth = dates.stringMonths()[month - 1].lower()
        if endMonth == month:
            monthsDays[stringMonth] = booking.departure.date.day
            return monthsDays

        monthDays = dates.daysInMonth(booking.arrival.date.year, month)
        if month == startMonth:
            monthDays -= booking.arrival.date.day
        monthsDays[stringMonth] = monthDays


def get_valid_bookings(start: datetime.date, end: datetime.date) -> list[Booking]:
    """
    Get valid bookings from the database.
    
    Parameters:
        database: The database connection.
        start: The start date for the bookings.
        end: The end date for the bookings.
        
    Returns:
        list: A list of valid bookings.
    """
    search = search_valid_bookings(start=start, end=end)
    
    select = search.guests.select()
    select.firstName()
    select.lastName()

    select = search.arrivals.select()
    select.date()

    select = search.departures.select()
    select.date()
    
    select = search.properties.select()
    select.name()
    select.priceId()

    select = search.charges.select()
    select.all()

    where = search.details.where()
    where.isOwner().isFalse()

    where = search.properties.where()
    where.weBook().isTrue()

    bookings = search.fetchall()
    database = search
    database.close()
    return bookings