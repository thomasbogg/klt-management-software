from datetime import date
from default.booking.booking import Booking
from default.booking.functions import (
    determine_extras_in_list,
    determine_flight_number,
    determine_flight_time,
    determine_hiring_a_car_in_string,
    determine_lisbon_in_string,
    determine_phonenumber,
    has_unconfirmed_status,
)
from default.database.database import Database
from default.database.functions import (
    get_booking,
    get_database,
    get_guest,
    get_property,
    search_valid_bookings
)
from default.settings import PLATFORMS, VALID_BOOKING_STATUSES
from default.update.dates import updatedates
from default.update.wrapper import update
from default.updates.functions import (
    arrival_date_has_changed,
    check_booking_updates,
    departure_date_has_changed,
    get_checkpoint_booking,
    is_cancelled_booking,
    property_has_changed,
)
from PIMS.browser import BrowsePIMS
from utils import log, logerror, string_is_affirmative, sublog


# Main entry point function
@update
def download_latest_from_PIMS(start: date = None, end: date = None, PIMSId: str | int | list = None, 
                             updatedSince: int = 2, visible: bool = False) -> str:
    """
    Download the latest booking data from PIMS to the local database.
    
    If PIMSId is provided, downloads only that specific booking.
    Otherwise, downloads all bookings within the date range that have been updated
    within the specified number of days.
    
    Parameters:
        start: Start date for filtering bookings
        end: End date for filtering bookings
        PIMSId: Specific booking ID(s) to download
        updatedSince: Only download bookings updated in the last N days
        visible: Whether to show the browser window during execution
    
    Returns:
        Success message confirming download
    """
    browser = BrowsePIMS(visible).goTo().login()
    database = get_database()
    log('Logged into PIMS.')

    if PIMSId:
        done = download_from_ids(database, browser.orderForms, PIMSId)
    else:
        if not start and not end:
            start, end = updatedates.PIMS_update_dates()

        reservations = get_reservations(browser.reservations.goTo(), start, end, updatedSince)
        log(f'Retrieved {len(reservations)} bookings to parse and update in database.')
        done = download_from_reservations_list(database, browser.orderForms, reservations, count=0)

    browser.quit()
    database.close()
    return done


# Booking download and processing functions
def download_from_ids(database: Database, orderForms: BrowsePIMS.OrderForms, 
                      PIMSId: str | int | list) -> str:
    """
    Download bookings by their PIMS IDs.
    
    Parameters:
        database: Database connection
        orderForms: PIMS order forms interface
        PIMSId: Single ID or list of IDs to download
    
    Returns:
        Success message
    """
    if isinstance(PIMSId, str) or isinstance(PIMSId, int):
        PIMSId = [PIMSId]

    for id in PIMSId: 
        booking = parse_order_form(database, orderForms, id)
        if not booking:
            logerror(f'Failed to update PIMS Booking @ id {id}')
            continue
        send_to_database(database, booking)

    return f'...SUCCESSFULLY downloaded latest for ORDER(S) {PIMSId} from PIMS!'


def get_reservations(reservations: BrowsePIMS.ReservationsList, start: date, end: date, 
                     updatedSince: int) -> list[dict]:
    """
    Configure search parameters and retrieve reservations from PIMS.
    
    Parameters:
        reservations: PIMS reservations list interface
        start: Start date for filtering bookings
        end: End date for filtering bookings
        updatedSince: Only return bookings updated in the last N days
    
    Returns:
        List of reservation dictionaries from PIMS
    """
    reservations.propertyName = 'All Properties'
    reservations.start = start
    reservations.end = end

    if updatedSince is not None:
        date = updatedates.calculate(days=-updatedSince)
        reservations.updatedSince = date
    else:
        reservations.updatedSince = updatedates.date(2020, 1, 1)

    reservations.resultsType = 'All data'
    reservations.sortBy = 'start_date'
    reservations.iCalOnly = False
    reservations.onlyOwner = False
    reservations.noOwner = False

    reservations.update()
    reservations.wait(1.5)
    return reservations.list


def download_from_reservations_list(database: Database, browser: BrowsePIMS.OrderForms, 
                                   reservations: list[dict], count: int) -> str:
    """
    Recursively process and download booking data from a list of reservations.
    
    Parameters:
        database: Database connection
        browser: PIMS order forms interface
        reservations: List of reservations to process
        count: Counter for processed bookings
    
    Returns:
        Success message with count of bookings downloaded
    """
    if not reservations:
        return f'...SUCCESSFULLY downloaded latest for {count} bookings from PIMS!'

    reservation = reservations.pop(0)
    PIMSId = reservation['orderId']

    if '(Not Available)' in reservation['guest']:
        return download_from_reservations_list(database, browser, reservations, count)

    if determine_enquiry_status(reservation['status']) not in VALID_BOOKING_STATUSES:
        exists = get_PIMS_booking(database, PIMSId)
        if exists and exists.statusIsNotOkay:
            return download_from_reservations_list(database, browser, reservations, count)

    booking = parse_order_form(database, browser, PIMSId)
    if not booking:
        return download_from_reservations_list(database, browser, reservations, count)

    send_to_database(database, booking)
    count += 1
    if count % 5 == 0:
        sublog(f'updated {count} bookings so far')

    return download_from_reservations_list(database, browser, reservations, count)


def parse_order_form(database: Database, browser: BrowsePIMS.OrderForms, 
                    PIMSId: str | int) -> Booking | None:
    """
    Extract booking details from a PIMS order form.
    
    Parameters:
        database: Database connection
        browser: PIMS order forms interface
        PIMSId: ID of the PIMS booking to parse
    
    Returns:
        Populated Booking object or None if parsing fails
    """
    booking = Booking(database)
    booking.details.PIMSId = PIMSId
    browser.goTo(PIMSId)

    if browser.propertyIsArchived: 
        return None
    
    if not browser.propertyName:
        return None

    booking = set_basic_booking_details(booking, browser)
    exists = get_PIMS_booking(database, PIMSId)

    if exists:
        booking.details.id = exists.details.id
        booking.details.guestId = exists.details.guestId
        booking.guest.id = exists.details.guestId
        booking.emails.management = exists.emails.management


    if browser.enquirySource != 'Direct':

        if 'A24' in browser.propertyName:
            booking.details.isOwner = True
            browser.ownerBooking = True
            browser.update()

        if exists:
            #set_booking_dates(booking, browser)
            return booking

        exists = get_platform_booking(
            database, browser.arrivalDate, browser.departureDate, booking.details.propertyName)
        if exists:
            booking.details.id = exists.details.id
            booking.details.guestId = exists.details.guestId
            return booking

    set_booking_dates(booking, browser)
    set_further_booking_details(booking, browser)

    if browser.ownerBooking:
        if exists and exists.forms.arrivalQuestionnaire:
            return booking

    set_remaining_details(booking, browser)
    #try:
    #    set_remaining_details(booking, browser)
    #except Exception as e:
    #    logerror(f'Failed to update PIMS Booking @ id {PIMSId}')
    #    sublog(f'...threw Exception: {e}')
    #    return None

    return booking


def send_to_database(database: Database, booking: Booking) -> None:
    """
    Save a booking to the database with update checking.
    
    Parameters:
        database: Database connection
        booking: Booking object to save
    
    Returns:
        None
    """
    if booking.exists():
        check_for_updates(database, booking)
        booking.update()
    else:
        booking.insert()
    return None


# Booking data extraction and transformation functions
def set_basic_booking_details(booking: Booking, browser: BrowsePIMS.OrderForms) -> Booking:
    """
    Set the core booking details from the order form.
    
    Parameters:
        booking: Booking object to update
        browser: PIMS order form interface
    
    Returns:
        Updated booking object
    """
    booking.details.propertyId = browser.propertyName
    booking.details.enquirySource = browser.enquirySource
    booking.details.isOwner = browser.ownerBooking
    booking.forms.PIMSoid = determine_oid(browser.myBookingForm)
    booking.forms.PIMSuin = determine_uin(browser.myBookingForm)
    return booking


def set_booking_dates(booking: Booking, browser: BrowsePIMS.OrderForms) -> None:
    """
    Set arrival or departure details from PIMS order form.
    
    Parameters:
        booking: Arrival or departure section of booking object
        time: Time string from PIMS
        orderFormDetails: Flight details from PIMS

    Returns:
        None
    """
    booking.arrival.date = browser.arrivalDate
    booking.departure.date = browser.departureDate
    return None


def set_further_booking_details(booking: Booking, browser: BrowsePIMS.OrderForms) -> Booking:
    """
    Set additional booking details from the order form.
    
    Parameters:
        booking: Booking object to update
        browser: PIMS order form interface
    
    Returns:
        Updated booking object
    """
    booking.details.enquiryStatus = determine_enquiry_status(browser.enquiryStatus)
    booking.details.enquiryDate = browser.enquiryDate
    booking.details.adults = browser.adults
    booking.details.children = browser.children
    booking.details.babies = browser.babies

    firstName, lastName = determine_guest_names(browser.firstName, browser.lastName, booking)
    booking.guest.firstName = firstName
    booking.guest.lastName = lastName

    return booking


def set_remaining_details(booking: Booking, browser: BrowsePIMS.OrderForms) -> None:
    """
    Set remaining details for a booking from PIMS order form.
    
    Includes guest details, arrival/departure information, extras, 
    owner options, and payment details.
    
    Parameters:
        booking: Booking object to update
        browser: PIMS order form interface
    
    Returns:
        None
    """
    # GUEST DETAILS
    booking.guest.email = None if not browser.email else browser.email.lower()
    booking.guest.phone = determine_phonenumber(browser.phone)
    booking.guest.nifNumber = browser.nifNumber

    ## TEMPORARY GUEST MATCHING TO AVOID DUPLICATE AND EMPTY GUESTS IN DATABASE ---
    #databaseGuestId = get_guest(booking)
    #if not databaseGuestId:
    #    logerror(f'Guest not found for booking with PIMSId {booking.details.PIMSId}, email {booking.guest.email}, phone {booking.guest.phone}, name {booking.guest.firstName} {booking.guest.lastName}')
    #    return None
    #booking.details.guestId = databaseGuestId

    # ARRIVAL & DEPARTURE DETAILS
    set_arrival_departure(booking.arrival, browser.arrivalTime, browser.inboundFlight)
    set_arrival_departure(booking.departure, browser.departureTime, browser.outboundFlight)
    
    # EXTRAS
    extras = booking.extras
    extras.airportTransfers = False
    extras.airportTransferInboundOnly = False
    extras.airportTransferOutboundOnly = False
    extras.cot = False
    extras.highChair = False
    extras.welcomePack = False
    extras.welcomePackModifications = ''
    extras.lateCheckout = False
    extras.midStayClean = False
    extras.otherRequests = list()
    determine_extras_in_list(browser.extras.split(' // '), booking)
    extras.otherRequests = ' // '.join(extras.otherRequests)
    
    # OWNER OPTIONS
    if booking.details.isOwner:
        if 'block' in booking.guest.lastName.lower():
            booking.arrival.meetGreet = False 
            booking.departure.clean = False
        else:
            set_owner_options(booking, browser) 
    else:
        booking.arrival.meetGreet = True
        booking.departure.clean = True
    
    # PAYMENT DETAILS
    charges = booking.charges
    charges.currency = determine_currency(browser.currency)

    if 'bank' in browser.paymentMethod.lower():
        charges.creditCard, charges.bankTransfer = False, True
    else:
        charges.creditCard, charges.bankTransfer = True, False

    charges.basicRental = browser.basicRental
    charges.admin = browser.adminFee
    charges.security = browser.securityCharge
    charges.securityMethod = determine_security_deposit_method(browser.securityChargeMethod)
    
    return None


def set_arrival_departure(booking, time: str, orderFormDetails: str) -> None:
    """
    Set arrival or departure details from PIMS order form.
    
    Parameters:
        booking: Arrival or departure section of booking object
        time: Time string from PIMS
        orderFormDetails: Flight details from PIMS
    
    Returns:
        None
    """
    flightNumber = determine_flight_number(orderFormDetails)
    
    if flightNumber:
        booking.flightNumber = flightNumber
        booking.time = determine_flight_time(orderFormDetails)
        booking.isFaro = not determine_lisbon_in_string(orderFormDetails)
        booking.details = '' if not determine_hiring_a_car_in_string(orderFormDetails) else 'Hiring a Car'
    else:
        booking.time = time
        booking.details = orderFormDetails
        booking.flightNumber = None
    
    return None


def set_owner_options(booking: Booking, browser: BrowsePIMS.OrderForms) -> None:
    """
    Set meet & greet and clean preferences for owner bookings.
    
    Parameters:
        booking: Booking object to update
        browser: PIMS order form interface
    
    Returns:
        None
    """
    meetGreet, clean = strings_are_affirmative(browser.ownerMeetGreet, browser.ownerClean)
    if meetGreet and clean:
        booking.arrival.meetGreet = meetGreet
        booking.departure.clean = clean
        return None
    
    meetGreet, clean = owner_defaults(booking)
    booking.arrival.meetGreet = meetGreet
    booking.departure.clean = clean
    return None


# Database query functions
def get_PIMS_booking(database: Database, PIMSId: str | int) -> Booking | None:
    """
    Get a booking from the database by PIMS ID.
    
    Parameters:
        database: Database connection
        PIMSId: PIMS booking ID to search for
    
    Returns:
        Booking object if found, None otherwise
    """
    search = get_booking(database, PIMSId=PIMSId)
    
    select = search.details.select()
    select.enquiryStatus()
    select.platformId()
    
    select = search.emails.select()
    select.management()

    select = search.forms.select()
    select.arrivalQuestionnaire()
    return search.fetchone()


def get_platform_booking(database: Database, arrivalDate: date, 
                        departureDate: date, propertyName: str) -> Booking | None:
    """
    Find a platform booking by dates and property.
    
    Parameters:
        database: Database connection
        arrivalDate: Booking arrival date
        departureDate: Booking departure date
        propertyName: Property name or ID
    
    Returns:
        Booking object if found, None otherwise
    """
    search = search_valid_bookings(database, propertyName=propertyName)

    select = search.details.select()
    select.platformId()
    
    where = search.arrivals.where()
    where.date().isEqualTo(arrivalDate)
    
    where = search.departures.where()
    where.date().isEqualTo(departureDate)
    
    where = search.details.where()
    where.PIMSId().isNullEmptyOrFalse()
    return search.fetchone()


def get_owner_booking(database: Database, PIMSId: str | int) -> Booking | None:
    """
    Get owner booking details from the database by PIMS ID.
    
    Parameters:
        database: Database connection
        PIMSId: PIMS booking ID to search for
    
    Returns:
        Booking object if found, None otherwise
    """
    search = get_booking(database, PIMSId=PIMSId)

    select = search.details.select()
    select.isOwner()
    select.platformId()

    select = search.properties.select()
    select.name()

    select = search.guests.select()
    select.firstName()
    select.lastName()

    select = search.emails.select()
    select.management()
    return search.fetchone()


def check_for_updates(database: Database, updatedBooking: Booking) -> None:
    """
    Check for significant updates to a booking that require notification.
    
    Parameters:
        database: Database connection
        updatedBooking: Updated booking to check for changes
    
    Returns:
        None
    """
    if updatedBooking.details.isPlatform:
        return
    if updatedBooking.guest.isBlock:
        return
    if has_unconfirmed_status(updatedBooking):
        return
    
    databaseBooking = get_checkpoint_booking(database, updatedBooking.details.id)
    if not databaseBooking.emails.management:
        return

    if updatedBooking.details.isOwner:
        if is_cancelled_booking(databaseBooking, updatedBooking):
            return
        if property_has_changed(databaseBooking, updatedBooking):
            return
        if arrival_date_has_changed(databaseBooking, updatedBooking):
            return
        if departure_date_has_changed(databaseBooking, updatedBooking):
            return
        return

    check_booking_updates(databaseBooking, updatedBooking)


# Utility functions
def determine_oid(form: str | None) -> str | None:
    """
    Extract the 'oid' parameter from a form URL.
    
    Parameters:
        form: URL string containing the form parameters
    
    Returns:
        The oid value if found, None otherwise
    """
    try:
        return form.split('oid=')[1].split('&')[0]
    except:
        return None
    

def determine_uin(form: str | None) -> str | None:
    """
    Extract the 'uin' parameter from a form URL.
    
    Parameters:
        form: URL string containing the form parameters
    
    Returns:
        The uin value if found, None otherwise
    """
    try:
        return form.split('uin=')[1].split('&')[0]
    except:
        return None


def determine_enquiry_status(string: str) -> str:
    """
    Determine the booking status from a status string.
    
    Maps PIMS status strings to standardized status values:
    - Maps various confirmed statuses to 'Booking confirmed'
    - Maps cancelled statuses to 'Booking cancelled'
    - Otherwise returns the capitalized status
    
    Parameters:
        string: Status string from PIMS
    
    Returns:
        Standardized status string
    """
    confirmed_statuses = (
        'Confirmed Booking', 
        'Holiday started', 
        'Holiday ended', 
        'Closed')
    for status in confirmed_statuses:
        if status in string:
            return 'Booking confirmed'
    
    cancelled_statuses = (
        'Cancelled', 
        'Dead')
    for status in cancelled_statuses:
        if status in string:
            return 'Booking cancelled'
    
    return string.split('  ')[0].capitalize()


def determine_guest_names(first: str | None, last: str, 
                         booking: Booking) -> tuple[str | None, str]:
    """
    Determine the guest's first and last name from PIMS data.
    
    Handles special cases like blocked periods, unknown guests, and platform bookings.
    
    Parameters:
        first: First name from PIMS
        last: Last name from PIMS
        booking: Booking object with property details
    
    Returns:
        Tuple of (first_name, last_name) with appropriate defaults for special cases
    """
    if 'block ' in last.lower():
        return None, last

    unknowns = (
        'not available', 
        'closed')
    for unknown in unknowns:
        if unknown in last.lower(): 
            return str(booking.details.propertyId), str(booking.details.PIMSId)

    split = last.split(' - ')
    if split[0] in PLATFORMS: 
        if not first: 
            first = split[1].split()[0]
        last = split[1].split()[-1]
        return first, last

    if len(split) > 1: 
        return 'Owner/Family', booking.details.PIMSId

    return first.title(), last.title()


def determine_security_deposit_method(string: str | None) -> str:
    """
    Determine security deposit method from PIMS string.
    
    Parameters:
        string: Security deposit method string from PIMS
    
    Returns:
        'Cash' if string is empty, otherwise the original string
    """
    if not string:
        return 'Cash'
    return string


def determine_currency(string: str) -> str:
    """
    Determine currency code from a string.
    
    Parameters:
        string: Currency string from PIMS
    
    Returns:
        'EUR' if 'eur' is in the string (case insensitive), 'GBP' otherwise
    """
    if 'eur' in string.lower():
        return 'EUR'
    return 'GBP'


def strings_are_affirmative(x: str | None, y: str | None) -> tuple[bool, bool]:
    """
    Check if two strings both indicate affirmative responses.
    
    Parameters:
        x: First string to check
        y: Second string to check
    
    Returns:
        Tuple of booleans indicating whether each string is affirmative
    """
    return string_is_affirmative(x), string_is_affirmative(y)


def owner_defaults(booking: Booking) -> tuple[bool, bool]:
    """
    Get default meet & greet and clean preferences for an owner booking.
    
    Parameters:
        booking: Booking object with property ID
    
    Returns:
        Tuple of (defaultMeetGreet, defaultClean) for the property owner
    """
    search = get_property(booking.details.propertyId)
    select = search.propertyOwners.select()
    select.defaultMeetGreet()
    select.defaultClean()
    property = search.fetchone()
    return property.owner.defaultMeetGreet, property.owner.defaultClean


def get_guest(booking: Booking) -> int | None:
    """
    Get the guest ID from the database based on booking details.
    
    Parameters:
        booking: Booking object with guest details to search for
    Returns:
        Guest ID if found, None otherwise 
    """
    from default.database.functions import search_guests
    search = search_guests()

    where = search.guests.where()

    if booking.guest.email:
        where.email().isEqualTo(booking.guest.email)
    
    if not booking.guest.email and booking.guest.phone:
        where.phone().isEqualTo(booking.guest.phone)

    if not booking.guest.email and not booking.guest.phone and booking.guest.firstName and booking.guest.lastName:
        where.firstName().isEqualTo(booking.guest.firstName)
        where.lastName().isEqualTo(booking.guest.lastName)

    result = search.fetchone()

    search.close()
    return result.id if result else None