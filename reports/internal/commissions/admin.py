import datetime

from default.booking.booking import Booking
from default.booking.functions import logbooking
from default.dates import dates
from default.database.functions import get_database, search_valid_bookings 
from default.update.wrapper import update


@update
def calculate_net_admin_fees(
    start: datetime.date = dates.firstOfYear(), 
    end: datetime.date = dates.lastOfYear()) -> str:
    """
    Calculate the net admin fees for a given period.

    Args:
        start: The start date of the period.
        end: The end date of the period.

    Returns:
        A message indicating the result of the calculation.
    """
    database = get_database()
    bookings = _get_bookings(database, start, end)

    totalNet = 0
    for booking in bookings:
        admin = booking.charges.admin
      
        if booking.charges.bankTransfer:
            totalNet += admin

        elif booking.charges.creditCard:
            origin = _determine_guest_origin(booking)
            if origin == 'uk':
                totalNet += _uk_card_charge(admin)
            elif origin == 'eea':
                totalNet += _eea_card_charge(admin)
            elif origin == 'international':
                totalNet += _international_card_charge(admin)
            else:
                logbooking(booking, inline='No phone or nationality for guest:')

    database.close()
    return f'Successfully calculated {start.year} Net Admin Fees: €{totalNet:,.2f}'


def _get_bookings(
        database, 
        start: datetime.date, 
        end: datetime.date) -> list[Booking]:
    """
    Get the bookings for a given period.

    Args:
        database: The database connection.
        start: The start date of the period.
        end: The end date of the period.

    Returns:
        A list of bookings for the specified period.
    """
    search = search_valid_bookings(database, start=start, end=end)

    select = search.guests.select()
    select.phone()
    select.nationality()
    select.firstName()
    select.lastName()

    select = search.charges.select()
    select.admin()
    select.bankTransfer()
    select.creditCard()
    select.currency()

    select = search.properties.select()
    select.shortName()

    select = search.arrivals.select()
    select.date()

    select = search.departures.select()
    select.date()

    where = search.details.where()
    where.enquirySource().isEqualTo('Direct')
    where.isOwner().isFalse()

    return search.fetchall()


def _determine_guest_origin(booking: Booking) -> str:
    """
    Get the origin country of the guest based on the booking information.
    Check the guest's nationality and phone number.

    Args:
        booking (Booking): The booking object containing guest details.

    Returns:
        str: The origin country of the guest.
    """
    nationality = booking.guest.nationality
    if nationality:
        nationality = nationality.strip().lower()
        if nationality in ('uk', 'united kingdom'):
            return 'uk'
        if nationality in _eea_countries():
            return 'eea'
        return 'international'

    phone = booking.guest.phone
    if not phone:
        return ''

    phone = phone.strip()
    if '+' in phone[0] or phone[0:2] == '00':
        phone = phone[1:] if phone[0] == '+' else phone[2:]

        if phone[1] in ('3', '4'):
            if phone[2] == '4':
                return 'uk'
            return 'eea'
        
    if phone[:2] == '07':
        return 'uk'
    
    if phone[:2] in ('91', '92', '93', '96'):
        return 'eea' 

    return 'international'


def _international_card_charge(fee: float) -> float:
    """
    Calculate the international card charge based on the fee.

    Args:
        fee: The fee to calculate the charge for.

    Returns:
        The calculated international card charge.
    """
    fraction = 1 - (3.25 / 5.5)
    return fee * fraction - .25


def _eea_card_charge(fee: float) -> float:
    """
    Calculate the EEA card charge based on the fee.

    Args:
        fee: The fee to calculate the charge for.

    Returns:
        The calculated EEA card charge.
    """
    fraction = 1 - (1.5 / 5.5)
    return fee * fraction - .25


def _uk_card_charge(fee: float) -> float:
    """
    Calculate the UK card charge based on the fee.

    Args:
        fee: The fee to calculate the charge for.

    Returns:
        The calculated UK card charge.
    """
    fraction = 1 - (2.5 / 5.5)
    return fee * fraction - .25


def _eea_countries() -> list[str]:
    return [
        'belgium',
        'spain',
        'hungary',
        'slovakia',
        'bulgaria',
        'france',
        'malta',
        'finland',
        'czechia',
        'croatia',
        'netherlands',
        'sweden',
        'denmark',
        'italy',
        'austria',
        'germany',
        'cyprus',
        'poland',
        'iceland',
        'estonia',
        'latvia',
        'portugal',
        'liechtenstein',
        'ireland',
        'lithuania',
        'romania',
        'norway',
        'greece',
        'luxembourg',
        'slovenia',
    ]