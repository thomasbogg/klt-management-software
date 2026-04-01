from correspondence.self.functions import new_email_to_self
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import (
    get_booking,
    get_database,
    get_property_price,
)
from default.dates import dates
from default.google.mail.functions import get_inbox
from default.property.prices import Prices
from default.settings import PROPERTIES, TEST
from default.update.wrapper import update
from platforms.bookingCom.browser import BrowseBookingComExtranet
from platforms.bookingCom.reader import ReadBookingComEmails
from platforms.functions import convert_date, update_booking_in_database
from utils import break_up_person_names, string_to_float, string_to_int


#######################################################
# MAIN UPDATE FUNCTIONS
#######################################################

@update
def update_from_bookingCom(
    start: str | None = None, 
    end: str | None = None, 
    properties: list[str] = PROPERTIES
) -> str:
    """
    Update bookings from Booking.com for specified dates and properties.
    
    Parameters:
        start: Start date for booking retrieval. If None, uses emails.
        end: End date for booking retrieval. If None, uses emails.
        properties: List of property names to update. Defaults to all properties.
        
    Returns:
        String indicating update result.
    """
    if not start and not end: 
        messages = get_inbox(sender='noreply@booking.com', subject='booking')
        if not messages: 
            return 'Not updating today!'
            
    browser = BrowseBookingComExtranet().goTo().login()
    database = get_database()
    
    if start and end: 
        done = update_from_dates(database, browser, start, end, properties)
    else: 
        reader = ReadBookingComEmails(messages)
        done = update_from_emails(database, browser, reader, properties)
        reader.deleteRead()
        
    browser.quit()
    database.close()
    return done


def update_from_dates(
    database: Database, 
    browser: BrowseBookingComExtranet, 
    start: str, 
    end: str, 
    properties: list[str]
) -> str:
    """
    Update bookings from Booking.com for the specified date range.
    
    Parameters:
        database: Database connection.
        browser: Browser instance for web scraping.
        start: Start date for booking retrieval.
        end: End date for booking retrieval.
        properties: List of property names to update.
        
    Returns:
        Success message.
    """
    for property in properties: 
        parse_property_reservations_page_bookings(database, browser, start, end, property)
    return 'Successfully scraped and parsed Booking.com bookings from given dates!'


def update_from_emails(
    database: Database, 
    browser: BrowseBookingComExtranet, 
    reader: ReadBookingComEmails, 
    properties: list[str]
) -> str:
    """
    Update bookings from Booking.com based on email notifications.
    
    Parameters:
        database: Database connection.
        browser: Browser instance for web scraping.
        reader: Email reader containing booking dates.
        properties: List of property names to update.
        
    Returns:
        Success message.
    """
    dates = (reader.quintaDaBarracudaDates, reader.clubeDoMonacoDates, reader.parqueDaCorcovadaDates)
    
    for i, (start, end) in enumerate(dates):
        if start is None or end is None:
            continue
        parse_property_reservations_page_bookings(database, browser, start, end, properties[i])
        
    return 'Successfully scraped and parsed Booking.com bookings from read emails!'


def delete_sign_in_email() -> str:
    """
    Delete sign-in notification emails from Booking.com.
    
    Returns:
        Message indicating number of deleted emails.
    """
    messages = get_inbox(sender='noreply@booking.com', subject='new sign-in')
    
    for message in messages:
        message.delete()
        
    return f'Deleted {len(messages)} sign-in emails.'


#######################################################
# RESERVATION PARSING FUNCTIONS
#######################################################

def parse_property_reservations_page_bookings(
    database: Database, 
    browser: BrowseBookingComExtranet,
    start: str, 
    end: str, 
    property: str
) -> None:
    """
    Retrieve and process property reservations from Booking.com.
    
    Parameters:
        database: Database connection.
        browser: Browser instance for web scraping.
        start: Start date for booking retrieval.
        end: End date for booking retrieval.
        property: Name of the property to retrieve bookings for.
        
    Returns:
        None
    """
    reservations = browser.propertyPage(property).reservations(start, end)
    
    if TEST: 
        print(f"Reservations for {property} between {start} and {end}:")
        reservationsList = reservations.list_reservations(reservations.html, test=True)
        for reservation in reservationsList:
            print(reservation)
            print('-----------')
        print('=======================================')
    
    for reservation in reservations.list:
        bookings = set_booking(database, reservation)
        for booking in bookings:
            if TEST:
                print(f"Bookings for {property} between {start} and {end}:")
                print(booking)
                print('-----------')
                continue
            update_booking_in_database(database, booking)


def set_booking(database: Database, reservation: dict[str, str]) -> list[Booking]:
    """
    Create Booking objects from reservation data.
    
    Parameters:
        database: Database connection.
        reservation: Dictionary containing reservation details.
        
    Returns:
        List of Booking objects created from the reservation.
    """
    bookings = list()
    arrivalDate = convert_date(reservation['check-in'])
    departureDate = convert_date(reservation['check-out'])
    enquiryDate = convert_date(reservation['booked'])
    databaseMonth = dates.stringMonths()[arrivalDate.month - 1].lower()
    propertiesFractions = parse_properties(reservation, databaseMonth, arrivalDate.year)
    totalProperties = len(propertiesFractions)

    """if totalProperties > 1:
        user, message = new_email_to_self(
            subject='Booking.com Multi-Property Booking Detected')

        body = message.body
        body.paragraph(
            'A Booking.com reservation has been detected that includes multiple properties. ' \
            'Need to sort guests accordingly.')
        body.paragraph(
            f'Arrival Date: {arrivalDate}, Departure Date: {departureDate}, Booked On: {enquiryDate}')

        message.send()
    """
    for name, fraction, num in propertiesFractions:
        booking = Booking(database)
        booking.details.enquirySource = 'Booking.com'
        booking.details.propertyId = name
        
        namesAndGuests = reservation['guest'].split('   ')
        firstNames, lastNames = break_up_person_names(namesAndGuests[0])
        booking.guest.firstName = firstNames
        booking.guest.lastName = lastNames
        
        if totalProperties > 1:
            adults, children, babies = sort_guests(reservation['Properties'][name].split('   '))
        else:
            adults, children, babies = sort_guests(namesAndGuests[1:])
            
        booking.details.adults = adults
        booking.details.children = children
        booking.details.babies = babies
        booking.arrival.date = arrivalDate
        booking.departure.date = departureDate
        booking.details.enquiryDate = enquiryDate
        booking.charges.currency = 'EUR'
        
        platformRentalCharge = string_to_float(reservation['price'].split('  ')[0]) * fraction
        platformFee = string_to_float(reservation['commission']) * fraction
        booking.charges.basicRental = platformRentalCharge - platformFee
        booking.charges.platformFee = platformFee
        booking.charges.admin = 0
        booking.details.enquiryStatus = sort_enquiry_status(reservation['status'], platformRentalCharge)
        
        if totalProperties > 1: 
            num = decide_booking_num_order(database, reservation, totalProperties, name, num)
            
        booking.details.platformId = f'{reservation["booking"]}-{num}'
        bookings.append(booking)
        
    return bookings


#######################################################
# PROPERTY AND GUEST RELATED HELPER FUNCTIONS
#######################################################

def parse_properties(
    reservation: dict[str, str], 
    databaseMonth: str,
    year: int
) -> list[tuple[str, float, int]]:
    """
    Parse property information from reservation data.
    
    Parameters:
        reservation: Dictionary containing reservation details.
        databaseMonth: Month name used in the database.
        year: Year of the reservation.
        
    Returns:
        List of tuples with property name, price fraction, and index.
    """
    propertyNames = reservation['rooms'].split(',')
    
    if len(propertyNames) == 1: 
        return [(propertyNames[0].strip(), 1, 0)]
        
    propertyNames = [name.split('1 x')[-1].strip() for name in propertyNames]
    prices = [get_price(name, databaseMonth, year) for name in propertyNames]
    fractions = [price / sum(prices) for price in prices]
    result = [(propertyNames[i], fractions[i], i) for i in range(len(propertyNames))]
    
    return result


def decide_booking_num_order(
    database: Database, 
    reservation: dict[str, str], 
    totalProps: int, 
    propName: str, 
    num: int, 
    count: int = 0
) -> int:
    """
    Determine the booking number order for multi-property reservations.
    
    Parameters:
        database: Database connection.
        reservation: Dictionary containing reservation details.
        totalProps: Total number of properties in the reservation.
        propName: Name of the property.
        num: Default number assignment.
        count: Current iteration count.
        
    Returns:
        Booking number order.
    """
    if count >= totalProps:
        return num
        
    platformId = f'{reservation["booking"]}-{count}'
    search = get_booking(database, platformId=platformId)
    search.properties.where().name().isEqualTo(propName)
    
    if search.fetchone(): 
        return count
        
    return decide_booking_num_order(database, reservation, totalProps, propName, num, count + 1)


def sort_guests(guestList: list[str]) -> tuple[int, int, int]:
    """
    Sort guests into adults, children, and babies.
    
    Parameters:
        guestList: List of guest information strings.
        apts: Number of apartments to distribute guests among.
        
    Returns:
        Tuple of (adults, children, babies) counts.
    """

    adults = string_to_int(guestList[0])
    children = 0
    babies = 0
    
    if len(guestList) < 2: 
        return adults, 0, 0
        
    ages = guestList[-1].split(',')
    
    for age in ages:
        number = string_to_int(age)
        if number > 13: 
            adults += 1
        elif number > 1:
            children += 1
        else: 
            babies += 1
              
    return adults, children, babies


def sort_enquiry_status(statusString: str, priceOfReservation: float) -> str:
    """
    Determine the enquiry status based on the reservation status and price.
    
    Parameters:
        statusString: Status string from the reservation.
        priceOfReservation: Price of the reservation.
        
    Returns:
        Enquiry status string.
    """
    if 'OK' in statusString: 
        return 'Booking confirmed'
    elif priceOfReservation > 0: 
        return 'Booking cancelled with fees'
    else: 
        return 'Booking cancelled'


def get_price(name: str, databaseMonth: str, year: int) -> float:
    """
    Get the price for a property during a specific month.
    
    Parameters:
        database: Database connection.
        name: Property name.
        databaseMonth: Month name used in the database.
        
    Returns:
        Price value.
    """
    search = get_property_price(name=name, month=databaseMonth, year=year)
    prices: Prices = search.fetchone().prices
    return prices.month(databaseMonth)


def test_reservations_page(filename: str = 'test-bookingcom.html') -> None:
    from web.html import HTML
    html = open(filename).read()
    parsed = BrowseBookingComExtranet.list_reservations(html, test=True)
    for reservation in parsed: 
        print(reservation)
        print('-----------')