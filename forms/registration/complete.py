from datetime import date
import random
from string import ascii_letters

from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import (
    get_database, 
    search_bookings, 
    set_enquiry_sources, 
    search_valid_bookings, 
    set_valid_accounts_booking,
)
from default.guest.guest import Guest
from default.update.dates import updatedates
from default.update.wrapper import update
from utils import logwarning, log


@update
def complete_empty_guest_details(start: date = None, end: date = None) -> None:
    """
    Complete empty guest details by checking for unregistered guests and updating their information.

    :param start: The start date for the search.
    :param end: The end date for the search.

    :return: A message indicating the completion status.
    """
    if start is None:
        start, end = updatedates.complete_empty_guest_details_dates()

    database = get_database()
    unregGuests = get_unregistered_guests(database, start, end)

    for booking in unregGuests:
        guest = booking.guest

        if guest.phone is None:
            logwarning(f'No Phone Number available for: {guest.name}')
            continue
      
        prevGuest = get_guest_with_same_phone_extension(database, guest.phone)
        if prevGuest is None:
            continue

        if prevGuest.nifNumber is None:
            guest.idCard = randomise_id(prevGuest.idCard[:11])
        else:
            guest.nifNumber = randomise_id(prevGuest.nifNumber)

        guest.nationality = prevGuest.nationality
        guest.update()
        log(
            f'Updated guest {guest.name} with details, NTL: {guest.nationality}, '
            f'ID: {guest.idCard}, NIF: {guest.nifNumber}'
        )

    database.close()
    return 'Successfully completed empty guest details.'


def get_unregistered_guests(database: Database, start: date, end: date) -> list[Booking]:
    """
    Search for unregistered guests within a specific date range.
    
    :param database: The database connection to use for the search.
    :param start: The start date for the search.
    :param end: The end date for the search.

    :return: A list of Guest objects that match the search criteria.
    """
    search = search_bookings(database=database)
    select = search.guests.select()
    select.all()

    select = search.properties.select()
    select.shortName()

    where = search.departures.where()
    where.date().isLessThan(end)
    where.date().isGreaterThan(start)
    
    where = search.guests.where()
    where.nationality().isNullEmptyOrFalse()
    where.nifNumber().isNullEmptyOrFalse()

    where = search.properties.where()
    where.weBook().isTrue()

    where = search.details.where()
    where.isOwner().isFalse()

    set_valid_accounts_booking(search)
    set_enquiry_sources(search, direct=False)
   
    return search.fetchall()
   

def get_guest_with_same_phone_extension(database: Database, phone: str) -> Guest | None:
    """
    Search for a guest with the same phone extension.

    :param database: The database connection to use for the search.
    :param phone: The phone number to search for.

    :return: A Guest object if found, otherwise None.
    """
    search = search_valid_bookings(database=database)
    select = search.guests.select()
    select.nationality()
    select.idCard()
    select.nifNumber()

    where = search.guests.where()
    where.phone().isLike(phone[:3])

    where = search.guests.where()
    where.nationality().isNotNullEmptyOrFalse()

    bookings = search.fetchall()

    if not bookings:
        logwarning(f'No guests found with phone extension: {phone[:3]}')
        return None

    randSelector = random.randint(0, len(bookings) - 1)
    guest = bookings[randSelector].guest
    return guest


def randomise_id(idCard: str) -> None:
    """
    Randomise the ID card number by replacing the last 4 digits with random numbers.
    
    :param idCard: The ID card number to be randomised.
    """
    if len(idCard) < 4:
        return idCard
  
    newId = idCard[:2]
    oldIdEnd = idCard[2:]
  
    for n in oldIdEnd:
        if not n.isdigit():
            newId += random.choice(ascii_letters.upper())
        else:
            newId += random.choice('0123456789')
    
    return newId
