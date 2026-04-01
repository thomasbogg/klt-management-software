from datetime import date
from PIMS.browser import BrowsePIMS
from correspondence.self.functions import new_bookings_email_to_self
from default.booking.booking import Booking
from default.booking.functions import logbooking
from default.database.database import Database
from default.database.functions import (
    get_booking, 
    search_valid_bookings,
    set_minimum_logging_criteria
)
from default.dates import dates
from default.updates.functions import (
    arrival_date_has_changed,
    departure_date_has_changed,
    guest_numbers_have_changed,
    is_cancelled_booking,
    property_has_changed
)
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from time import sleep
from utils import sublog


# Decorator for retry logic
def threeX(func):
    """
    Decorator that attempts to execute a function up to three times if it fails with NoSuchElementException.
    
    Useful for web scraping operations where elements might not load immediately.
    
    Parameters:
        func: The function to wrap with retry logic
        
    Returns:
        The wrapped function with retry logic
    """
    def wrapper(*args, **kwargs):
        for i in range(3):
            try:
                return func(*args, **kwargs)
            except (NoSuchElementException, TimeoutException):
                sleep(2 * (i + 1))

        sublog(f'FATAL : Tried 3 times to load web page.')
        sublog('------SKIPPING------')
        return None
        
    return wrapper


# Database update functions
def update_booking_in_database(database: Database, booking: Booking) -> None:
    """
    Update booking information in the database, handling existing records appropriately.
    
    Checks if the booking exists in the database and updates or inserts accordingly.
    Respects manual flags to avoid overwriting user-edited data.
    
    Parameters:
        database: Database connection
        booking: Booking object with updated information
        
    Returns:
        None
    """
    databaseBooking = find_database_match(database, booking)
    
    if not databaseBooking and not booking.statusIsOkay:
        return None
    
    if not databaseBooking:
        booking.arrival.meetGreet = True
        booking.departure.clean = True
        booking.insert()
        return None
    
    booking.details.id = databaseBooking.id
    
    if databaseBooking.details.manualGuests:
        del booking.details.adults
        del booking.details.children
        del booking.details.babies
    
    booking.details.update()
    
    if not databaseBooking.arrival.manualDate:
        booking.arrival.bookingId = databaseBooking.id
        booking.arrival.update()
    
    if not databaseBooking.departure.manualDate:
        booking.departure.bookingId = databaseBooking.id
        booking.departure.update()
    
    if not databaseBooking.charges.manualCharges:
        booking.charges.bookingId = databaseBooking.id
        booking.charges.update()
    
    if not databaseBooking.guest.email:
        booking.guest.id = databaseBooking.guest.id
        booking.guest.update()
    
    return None


def find_database_match(database: Database, booking: Booking) -> Booking | None:
    """
    Find a matching booking in the database using multiple search strategies.
    
    First tries to match by platform ID, then by basic booking characteristics,
    and finally by general characteristics.
    
    Parameters:
        database: Database connection
        booking: Booking object to match
        
    Returns:
        Matching booking if found, None otherwise
    """
    inDatabase = search_booking_by_platform_id(database, booking.details.platformId)
    
    if inDatabase:
        return return_exact_database_match(database, booking, inDatabase)
    
    if booking.details.enquiryStatus == 'Booking cancelled':
        return None
    
    inDatabase = search_booking_by_basic_characteristics(database, booking)
    
    if inDatabase:
        return get_booking_from_database(database, inDatabase.id)
    
    inDatabase = search_booking_by_general_characteristics(database, booking)
    
    if inDatabase:
        return get_booking_from_database(database, inDatabase.id)
    
    logbooking(booking, 'NEW BOOKING: found NO ids in database to match:')
    return None


def return_exact_database_match(database: Database, booking: Booking, 
                              inDatabase: Booking) -> Booking | None:
    """
    Process an exact database match, handling status changes and updates.
    
    Checks for updates that need notification and handles cancellations.
    
    Parameters:
        database: Database connection
        booking: New booking information
        inDatabase: Matched booking from database
        
    Returns:
        Database booking if active, None if cancelled
    """
    databaseBooking = get_booking_from_database(database, inDatabase.id)
    
    if databaseBooking.emails.management:
        check_updates_to_booking(databaseBooking, booking)
    
    if booking.statusIsOkay:
        return databaseBooking
    
    if databaseBooking.statusIsOkay:
        cancel_booking_in_PIMS(databaseBooking)
        databaseBooking.details.enquiryStatus = 'Booking cancelled'
        databaseBooking.details.update()
    
    return None


def search_booking_by_platform_id(database: Database, platformId: str) -> Booking | None:
    """
    Search for a booking in the database using its platform ID.
    
    Parameters:
        database: Database connection
        platformId: Platform-specific booking ID
        
    Returns:
        Matching booking if found, None otherwise
    """
    search = get_booking(database, platformId=platformId)
    return search.fetchone()


def search_booking_by_basic_characteristics(database: Database, booking: Booking) -> Booking | None:
    """
    Search for a booking by property, source, arrival and departure dates.
    
    Looks for bookings with the same property, source, and dates but without
    a platform ID and with a PIMS ID.
    
    Parameters:
        database: Database connection
        booking: Booking object with search criteria
        
    Returns:
        Matching booking if found, None otherwise
    """
    search = search_valid_bookings(database)
    
    where = search.details.where()
    where.propertyId().isEqualTo(booking.details.propertyId)
    where.enquirySource().isEqualTo(booking.details.enquirySource)
    where.platformId().isNullEmptyOrFalse()
    where.PIMSId().isNotNullEmptyOrFalse()
    
    search.arrivals.where().date().isEqualTo(booking.arrival.date)
    search.departures.where().date().isEqualTo(booking.departure.date)
    
    return search.fetchone()


def search_booking_by_general_characteristics(database: Database, booking: Booking) -> Booking | None:
    """
    Search for a booking by property, enquiry date and source.
    
    Looks for bookings with the same property, enquiry date and source but without
    a platform ID and with a PIMS ID.
    
    Parameters:
        database: Database connection
        booking: Booking object with search criteria
        
    Returns:
        Matching booking if found, None otherwise
    """
    search = search_valid_bookings(database)
    
    where = search.details.where()
    where.propertyId().isEqualTo(booking.details.propertyId)
    where.enquiryDate().isEqualTo(booking.details.enquiryDate)
    where.enquirySource().isEqualTo(booking.details.enquirySource)
    where.platformId().isNullEmptyOrFalse()
    where.PIMSId().isNotNullEmptyOrFalse()
    
    return search.fetchone()


def get_booking_from_database(database: Database, id: int) -> Booking:
    """
    Retrieve a booking from the database with all needed fields selected.
    
    Parameters:
        database: Database connection
        id: Booking ID
        
    Returns:
        Booking object with selected fields
    """
    search = get_booking(database, id)
    
    select = search.details.select()
    select.PIMSId()
    select.platformId()
    select.enquirySource()
    select.enquiryStatus()
    select.manualGuests()
    select.adults()
    select.children()
    select.babies()
    
    select = search.arrivals.select()
    select.date()
    select.manualDate()
    
    select = search.departures.select()
    select.date()
    select.manualDate()
    
    select = search.charges.select()
    select.manualCharges()
    
    select = search.extras.select()
    select.airportTransfers()
    select.airportTransferInboundOnly()
    select.airportTransferOutboundOnly()
    select.extraNights()
    
    select = search.properties.select()
    select.name()
    
    select = search.guests.select()
    select.id()
    select.firstName()
    select.lastName()
    select.email()
    
    select = search.emails.select()
    select.management()
    
    return search.fetchone()


def get_bookings_for_PIMS_updates(database: Database, platformIds: list[str]) -> list[Booking]:
    """
    Get bookings that need to be updated in PIMS.
    
    Parameters:
        database: Database connection
        platformIds: List of platform IDs to include
        
    Returns:
        List of bookings that need PIMS updates
    """
    search = search_valid_bookings(database)
    
    where = search.details.where()
    where.platformId().isIn(platformIds)
    
    select = search.details.select()
    select.PIMSId()
    select.adults()
    select.children()
    select.babies()
    
    select = search.arrivals.select()
    select.date()
    
    select = search.departures.select()
    select.date()
    
    select = search.charges.select()
    select.basicRental()
    select.currency()
    
    return search.fetchall()


# PIMS interaction functions
def cancel_booking_in_PIMS(databaseBooking: Booking) -> None:
    """
    Cancel a booking in the PIMS system.
    
    If the booking has no PIMS ID, emails a notification instead.
    
    Parameters:
        databaseBooking: Booking to cancel in PIMS
        
    Returns:
        None
    """
    logbooking(databaseBooking, 'CANCELLED BOOKING is still active in database:')
    PIMSId = databaseBooking.details.PIMSId
    
    if not PIMSId:
        subject = f'No PIMS record for cancelled Platform booking {databaseBooking.id}'
        new_bookings_email_to_self(subject=subject, bookings=[databaseBooking])
        return None
    
    sublog(f'active in PIMS @ {PIMSId}. Cancelling there now...')
    open_PIMS().goTo(PIMSId).cancelBooking().quit()
    sublog('booking successfully cancelled in PIMS.')
    
    return None


def update_PIMS_platform_bookings(database: Database, platformIds: list[str]) -> None:
    """
    Update platform booking details in the PIMS system.
    
    Updates arrival/departure dates, charges, and guest counts for
    the specified platform bookings.
    
    Parameters:
        database: Database connection
        platformIds: List of platform IDs to update in PIMS
        
    Returns:
        None
    """
    bookings = get_bookings_for_PIMS_updates(database, platformIds)
    
    if not bookings:
        return None
    
    browser = open_PIMS()
    
    for booking in bookings:
        browser.goTo(booking.details.PIMSId)
        browser.arrivalDate = booking.arrival.date
        browser.departureDate = booking.departure.date
        browser.basicRental = booking.charges.basicRental
        browser.adminFee = 0
        browser.currency = booking.charges.currency
        browser.adults = booking.details.adults
        browser.children = booking.details.children
        browser.babies = booking.details.babies
        browser.update()
    
    return browser.quit()


def open_PIMS() -> BrowsePIMS.OrderForms:
    """
    Open and initialize a PIMS browser session.
    
    Returns:
        PIMS order forms interface, ready for use
    """
    return BrowsePIMS(visible=False).goTo().login().orderForms


# Date conversion functions
def convert_dates(arrival: str, departure: str) -> tuple[date, date]:
    """
    Convert arrival and departure date strings to date objects.
    
    Handles multiple date format variations including:
    - 'Feb 8, 2024'
    - '8 Feb 2024'
    - '8 Feb'
    
    Parameters:
        arrival: Arrival date string
        departure: Departure date string
        
    Returns:
        Tuple of (arrival_date, departure_date) as date objects
    """
    # 'Feb 8, 2024' or '8 Feb 2024' or '8 Feb'
    arrival = arrival.replace(',', '').split()
    departure = departure.replace(',', '').split()

    if len(arrival) < 3:
        if len(departure) < 3:
            arrivalYear = departureYear = dates.year()
        else:
            arrivalYear = departureYear = departure[-1]
    else:
        arrivalYear = arrival[-1]
        if len(departure) < 3:
            departureYear = arrivalYear
        else:
            departureYear = departure[-1]

    if len(arrival) < 2:
        try:
            int(departure[1])
            arrivalMonth = departureMonth = departure[0]
            arrivalDay = departure[1]
        except ValueError:
            arrivalMonth = departureMonth = departure[1]
            arrivalDay = departure[0]    
    else:
        try:
            int(arrival[1])
            arrivalMonth = departureMonth = arrival[0]
            arrivalDay = arrival[1]
        except ValueError:
            arrivalMonth = arrival[1]
            arrivalDay = arrival[0]
    
    if len(departure) < 2:
        departureMonth = arrivalMonth
        departureDay = departure[0]
    else:
        try:
            int(departure[1])
            departureMonth = departure[0]
            departureDay = departure[1]
        except ValueError:
            departureMonth = departure[1]
            departureDay = departure[0]

    arrivalDate = dates.date(year=int(arrivalYear), month=dates.intMonth(arrivalMonth), day=int(arrivalDay))
    departureDate = dates.date(year=int(departureYear), month=dates.intMonth(departureMonth), day=int(departureDay))
    return arrivalDate, departureDate


def convert_date(date_str: str) -> date:
    """
    Convert a single date string to a date object.
    
    Handles multiple date format variations including:
    - 'Feb 8, 2024'
    - '8 Feb 2024'
    - '8 Feb'
    
    Parameters:
        date_str: Date string to convert
        
    Returns:
        Date object
    """
    # 'Feb 8, 2024' or '8 Feb 2024' or '8 Feb'
    date_parts = date_str.replace(',', '').split()

    if len(date_parts) < 3:
        year = dates.year()
    else:
        year = int(date_parts[-1])

    day = date_parts[0]
    month = date_parts[1]

    if len(day) > 2:
        x = day
        day = month
        month = x

    return dates.date(year=year, month=dates.intMonth(month), day=int(day))


# Update checking functions
def check_updates_to_booking(databaseBooking: Booking, updatedBooking: Booking) -> None:
    """
    Check for significant updates to a booking that require notification.
    
    Only checks fields that haven't been manually edited, as indicated by
    the manual flags.
    
    Parameters:
        databaseBooking: Original booking from database
        updatedBooking: New booking information to compare against
        
    Returns:
        None
    """
    if is_cancelled_booking(databaseBooking, updatedBooking):
        return None
    
    if property_has_changed(databaseBooking, updatedBooking):
        return None
    
    if databaseBooking.extras.extraNights:
        return None
    
    if not databaseBooking.arrival.manualDate:
        if arrival_date_has_changed(databaseBooking, updatedBooking):
            return None
    
    if not databaseBooking.departure.manualDate:
        if departure_date_has_changed(databaseBooking, updatedBooking):
            return None
        
    if not databaseBooking.details.manualGuests:
        if guest_numbers_have_changed(databaseBooking, updatedBooking):
            return None
    
    return None


def notify_platform_bookings_without_PIMS_ID(start: date = dates.firstOfYear(), end: date = dates.lastOfYear()) -> None:
    """
    Check the database for bookings without a PIMS ID and notify if found.
    
    Returns:
        None
    """
    database = search_valid_bookings(start=start, end=end)
    search = database

    set_minimum_logging_criteria(search)

    where = search.details.where()
    where.PIMSId().isNullEmptyOrFalse()
    where.platformId().isNotNullEmptyOrFalse()
    
    bookings = search.fetchall()
    
    if bookings:
        subject = f'Platform Bookings without PIMS ID - {dates.prettyDate()}'
        new_bookings_email_to_self(subject=subject, bookings=bookings)
    
    database.close()
    return None