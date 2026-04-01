from datetime import date
from default.booking import booking
from default.booking.booking import Booking
from default.booking.functions import (
    determine_extras_in_list,
    determine_flight_number,
    determine_hiring_a_car_in_string,
    determine_lisbon_in_string,
    determine_owner_family_in_name,
    determine_phonenumber
)
from default.database.database import Database
from default.dates import dates
from default.google.mail.functions import new_email, send_email
from default.property.property import Property
from default.updates.functions import (
    arrival_date_has_changed,
    arrival_flight_has_changed,
    arrival_time_has_changed,
    clean_has_changed,
    cot_changes,
    departure_date_has_changed,
    departure_flight_has_changed,
    departure_time_has_changed,
    guest_numbers_have_changed,
    high_chair_changes,
    is_cancelled_booking,
    late_checkout_changes,
    mid_stay_clean_changes
)
from default.workbook.functions import (
    cells_are_empty, 
    row_date_is_before_start_date
)
from sheets.functions import (
    cells, 
    check_for_border, 
    determine_departure_row, 
    get_property_sheet_booking,
    insert_empty_row, 
    set_latest_date_border,
    set_worksheet
)
from utils import (
    break_up_person_names, 
    isString,
    logwarning,
    only_digits_in_string,
    string_is_affirmative
)
from workbooks.worksheet import Worksheet


#######################################################
# WORKSHEET SETUP AND CONFIGURATION
#######################################################

def set_KKLJ_worksheet(
    worksheet: Worksheet, 
    property: Property, 
    start: date | int | None = None
) -> Worksheet:
    """
    Set the worksheet for the KKLJ properties.
    
    Parameters:
        worksheet: The worksheet object to set
        property: The property object to set in the worksheet
        start: The start date or row number for the worksheet
        
    Returns:
        The updated worksheet object
    """
    worksheet = set_worksheet(property.shortName, start)
    worksheet.row.defaultDelete = 1
    worksheet.propertyId = property.id
    worksheet.propertyName = property.name
    return worksheet


def update_worksheet(database: Database, worksheet: Worksheet) -> Worksheet:
    """
    Update a worksheet with booking data.
    
    Parameters:
        database: The database connection
        worksheet: The worksheet to update
        
    Returns:
        The updated worksheet
    """
    worksheet.row.number = worksheet.row.firstDataRow - 1
    _update_worksheet(database, worksheet)
    set_latest_date_border(worksheet)
    return worksheet


def _update_worksheet(database: Database, worksheet: Worksheet) -> Worksheet:
    """
    Recursively update a worksheet by processing rows and inserting bookings.
    
    Parameters:
        database: The database connection
        worksheet: The worksheet to be updated
        
    Returns:
        The updated worksheet
    
    This function processes rows recursively, checking conditions such as 
    empty cells, row dates, and booking IDs to determine the appropriate 
    action (insert, delete, or skip rows).
    """
    row = worksheet.row
    if row.atMaxEmpties:
        return worksheet

    row.increase()
    row.setHeight()

    check_for_border(worksheet)

    if cells_are_empty(worksheet, (2, 5)):
        insert_empty_row(worksheet)
        row.increaseEmptyCount()
        return _update_worksheet(database, worksheet)
    
    row.resetEmptyCount()

    if row_date_is_before_start_date(worksheet, 2):
        return _update_worksheet(database, worksheet)
    
    if determine_departure_row(worksheet):
        if not cells_are_empty(worksheet, (1,)):
            return _update_worksheet(database, worksheet)
    
    if cells_are_empty(worksheet, (1,)):
        get_new_booking(worksheet, database)
    elif cells_are_struck(worksheet):
        delete_booking(worksheet, database)
    else:
        update_booking(worksheet, database)
    
    return _update_worksheet(database, worksheet)


#######################################################
# BOOKING OPERATIONS
#######################################################

def get_new_booking(worksheet: Worksheet, database: Database) -> None:
    """
    Create a new booking from the worksheet data.
    
    Parameters:
        worksheet: The worksheet containing booking data
        database: The database connection
        
    Returns:
        None
    """
    row = worksheet.row
    row.arrival = row.number
    worksheet.column.number = 5
    row.departure = find_booking_departure_row(worksheet, name=worksheet.cell.value)

    if not row.departure:
        row.number = row.arrival
        worksheet.column.number = 5
        return send_unmatched_row_email(worksheet)

    booking = set_booking(database, worksheet.cell.value, worksheet)
    booking.details.enquiryDate = dates.date()
    parse_arrival_row(worksheet, booking)
    parse_departure_row(worksheet, booking)
    booking.save()
    
    booking = get_property_sheet_booking(database, booking.id)
    insert_booking_in_sheet(worksheet, booking)


def update_booking(worksheet: Worksheet, database: Database) -> None:
    """
    Update an existing booking in the worksheet and database.
    
    Parameters:
        worksheet: The worksheet containing booking data
        database: The database connection
        
    Returns:
        None
    """
    worksheet.column.reset()
    bookingId = worksheet.cell.value
    row = worksheet.row
    row.arrival = row.number
    row.departure = find_booking_departure_row(worksheet, bookingId)
    
    if not row.departure:
        logwarning(f'Booking {bookingId} not found in departure row')
        return None
    check_for_border(worksheet)

    databaseBooking = get_property_sheet_booking(database, worksheet.cell.value)
    updatedBooking = set_booking(database, bookingId, worksheet)
    updatedBooking.details.guestId = databaseBooking.details.guestId
    extractAllData = (
        not databaseBooking.property.sendOwnerBookingForms or 
        not databaseBooking.emails.arrivalQuestionnaire
    )
    parse_arrival_row(worksheet, updatedBooking, extractAllData=extractAllData)
    parse_departure_row(worksheet, updatedBooking, extractAllData=extractAllData)
    check_for_updates(databaseBooking, updatedBooking, extractAllData=extractAllData)
    updatedBooking.update()
    databaseBooking = get_property_sheet_booking(database, updatedBooking.id)
    
    insert_booking_in_sheet(worksheet, databaseBooking)


def delete_booking(worksheet: Worksheet, database: Database) -> None:
    """
    Delete a booking from the worksheet and database.
    
    Parameters:
        worksheet: The worksheet containing booking data
        database: The database connection
        
    Returns:
        None
    """
    worksheet.column.reset()
    bookingId = worksheet.cell.value
    row = worksheet.row
    row.arrival = row.number
    row.departure = find_booking_departure_row(worksheet, bookingId)
    if not row.departure:
        return None
    
    databaseBooking = get_property_sheet_booking(database, worksheet.cell.value)
    updatedBooking = set_booking(database, bookingId, worksheet)
    updatedBooking.details.enquiryStatus = 'Booking cancelled'
    if databaseBooking.emails.management:
        is_cancelled_booking(databaseBooking, updatedBooking)
    updatedBooking.details.update()

    row.number = row.arrival
    for _ in range(row.arrival, row.departure + 2):
        row.delete()
    row.decrease()


def set_booking(database: Database, bookingId: int, worksheet: Worksheet) -> Booking:
    """
    Create a booking object with data from the worksheet.
    
    Parameters:
        database: The database connection
        bookingId: The booking ID to set
        worksheet: The worksheet containing booking data
        
    Returns:
        The created booking object
    """
    booking = Booking(database)
    booking.details.id = bookingId
    booking.details.propertyId = worksheet.propertyId
    booking.details.enquirySource = 'KKLJ'
    booking.details.isOwner = True
    booking.details.enquiryStatus = 'Booking confirmed'
    return booking


#######################################################
# WORKSHEET ROW OPERATIONS
#######################################################

def cells_are_struck(worksheet: Worksheet) -> bool:
    """
    Check if any cells in the row are struck through (marked for deletion).
    
    Parameters:
        worksheet: The worksheet to check
        
    Returns:
        True if cells are struck through, False otherwise
    """
    column = worksheet.column
    for col in range(1, 6):
        column.number = col
        if worksheet.cell.isStruck:
            return True
    return False


def find_booking_departure_row(
    worksheet: Worksheet, 
    bookingId: int | None = None, 
    name: str | None = None
) -> int | None:
    """
    Find the departure row for a booking by ID or guest name.
    
    Parameters:
        worksheet: The worksheet to search
        bookingId: The booking ID to look for
        name: The guest name to look for
        
    Returns:
        Row number of the departure row or None if not found
    """
    row = worksheet.row
    row.increase()
    column = worksheet.column
    column.number = 1

    if bookingId and worksheet.cell.value == bookingId:
        return row.number
   
    column.number = 5
    if name and worksheet.cell.value == name:
        return row.number
    if name and not worksheet.cell.isEmpty or row.number - row.arrival > 4:
        return None
 
    return find_booking_departure_row(worksheet, bookingId)


def insert_booking_in_sheet(worksheet: Worksheet, booking: Booking | None) -> None:
    """
    Insert booking data into worksheet rows.
    
    Parameters:
        worksheet: The worksheet to update
        booking: The booking to insert
    """
    row = worksheet.row
    row.number = row.arrival

    difference = row.departure - row.arrival
    arrival = [(False, booking)]
    blanks = [(False, None)] * (difference - 1)
    departure = [(True, booking)]
   
    for boolean, booking in arrival + blanks + departure:
        worksheet.column.reset()
       
        for cell in cells():
            cell(worksheet, booking, isDeparture=boolean)
            worksheet.column.increase()

        if boolean and not worksheet.latestBorderRow:
            if booking.departure.date > dates.date():
                worksheet.latestBorderRow = row.number
        
        row.increase()
   
    row.decrease()
    worksheet.column.reset()


#######################################################
# DATA PARSING FUNCTIONS
#######################################################

def parse_arrival_row(
    worksheet: Worksheet, 
    booking: Booking, 
    extractAllData: bool = True
) -> Booking:
    """
    Parse booking data from the arrival row.
    
    Parameters:
        worksheet: The worksheet containing booking data
        booking: The booking object to update
        extractAllData: Whether to extract all data or just dates
        
    Returns:
        The updated booking object
    """
    worksheet.row.number = worksheet.row.arrival
    column = worksheet.column
    cell = worksheet.cell

    column.reset()
    booking.details.id = cell.value

    column.increase()
    booking.arrival.date = sort_date(cell.value)

    column.increase()
    if extractAllData:
        booking.arrival.time = cell.value

    column.increase()
    if extractAllData:
        booking.arrival.flightNumber = determine_flight_number(cell.value)
        if booking.arrival.flightNumber:
            booking.arrival.isFaro = not determine_lisbon_in_string(cell.value)
            booking.arrival.details = 'Hiring a Car' if determine_hiring_a_car_in_string(cell.value) else None 
        else:
            booking.arrival.details = cell.value

    column.increase()
    if extractAllData:
        booking.guest.firstName, booking.guest.lastName = determine_guest_name(worksheet.propertyName, cell.value)
  
    column.increase()
    if extractAllData:
        adults, children, babies = determine_group(cell.value)
        booking.details.adults = adults
        booking.details.children = children
        booking.details.babies = babies

    column.increase()
    if extractAllData:
        booking.guest.phone = determine_phonenumber(cell.value)
    
    column.increase()
    if extractAllData:
        booking.extras.cot = False
        booking.extras.highChair = False
        booking.extras.lateCheckout = False
        booking.extras.midStayClean = False
        booking.extras.welcomePack = False
        booking.extras.otherRequests = list()
        booking.extras.airportTransferInboundOnly = False
        booking.extras.airportTransferOutboundOnly = False
        booking.extras.airportTransfers = False
        booking.extras.extraNights = False
        booking.extras.otherRequests = list()
        extras = cell.value
        if extras:
            determine_extras_in_list(extras.split(','), booking)
    
    column.number = 11
    if extractAllData:
        booking.arrival.meetGreet = determine_clean_meet_greet(cell.value)
    
    column.increase()
    if extractAllData:
        booking.departure.clean = determine_clean_meet_greet(cell.value)

    return booking


def parse_departure_row(
    worksheet: Worksheet, 
    booking: Booking, 
    extractAllData: bool = True
) -> Booking:
    """
    Parse booking data from the departure row.
    
    Parameters:
        worksheet: The worksheet containing booking data
        booking: The booking object to update
        extractAllData: Whether to extract all data or just dates
        
    Returns:
        The updated booking object
    """
    worksheet.row.number = worksheet.row.departure
    column = worksheet.column
    cell = worksheet.cell

    column.reset()
    column.increase()
    booking.departure.date = sort_date(cell.value)

    column.increase()
    if extractAllData:
        booking.departure.time = cell.value

    column.increase()
    if extractAllData:    
        booking.departure.flightNumber = determine_flight_number(cell.value)
        if booking.departure.flightNumber:
            booking.departure.isFaro = not determine_lisbon_in_string(cell.value) 
            booking.departure.details = None
        else:
            booking.departure.details = cell.value

    column.number = 7
    if extractAllData:
        booking.guest.email = determine_email(cell.value)
    
    column.increase()
    if extractAllData:
        extras = cell.value
        if extras:
            determine_extras_in_list(cell.value.split(','), booking)
        booking.extras.otherRequests = ' // '.join(booking.extras.otherRequests)
        
    column.number = 11
    if extractAllData and booking.arrival.meetGreet is None:
        meetGreet = determine_clean_meet_greet(cell.value)
        booking.arrival.meetGreet = True if meetGreet is None else meetGreet
    
    column.increase()
    if extractAllData and booking.departure.clean is None:
        clean = determine_clean_meet_greet(cell.value)
        booking.departure.clean = True if clean is None else clean
    
    return booking


#######################################################
# DATA INTERPRETATION HELPERS
#######################################################

def determine_group(string: str | None) -> tuple[int, int, int]:
    """
    Parse guest group information from a string.
    
    Parameters:
        string: String containing group information (e.g. '2a 1c 1b')
        
    Returns:
        Tuple of (adults, children, babies) counts
    """
    adults = 2
    children = 0
    babies = 0
    if not string:
        return adults, children, babies

    string = string.strip().lower().split()
    for ageGroup in string:
        if 'a' in ageGroup:
            adults = int(only_digits_in_string(ageGroup))
        elif 'c' in ageGroup:
            children = int(only_digits_in_string(ageGroup))
        elif 'b' in ageGroup:
            babies = int(only_digits_in_string(ageGroup))
    
    return adults, children, babies


def determine_guest_name(propName: str, string: str | None) -> tuple[str, str]:
    """
    Determine guest first and last name from string.
    
    Parameters:
        propName: Property name to use if owner
        string: String containing guest name
        
    Returns:
        Tuple of (firstName, lastName)
    """
    if determine_owner_family_in_name(string):
        return propName, 'Owners/Family'
    return break_up_person_names(string)


@isString
def determine_email(string: str) -> str | None:
    """
    Extract email address from string.
    
    Parameters:
        string: String that may contain an email address
        
    Returns:
        Email address if found, None otherwise
    """
    if '@' in string:
        return string
    return None


def determine_clean_meet_greet(value: str | bool | int | None) -> bool | None:
    """
    Determine if a value indicates a clean or meet & greet is required.
    
    Parameters:
        value: Value to interpret
        
    Returns:
        True if clean/meet & greet is required, False if not, None if unclear
    """
    if value is None or value == '':
        return None
    if isinstance(value, (bool, int, float)):
        return bool(value)
    if isinstance(value, str):
        value = value.strip().lower()
        return string_is_affirmative(value)
    return None


def sort_date(value: str | date | None) -> date | None:
    """
    Convert various date formats to a date object.
    
    Parameters:
        value: Date value to process
        
    Returns:
        Date object or None if invalid
    """
    if not value:
        return None
    if dates.isDatetimeDatetime(value):
        return value.date()
    if dates.isDatetimeDate(value): 
        return value
    return None


#######################################################
# NOTIFICATION AND UPDATES
#######################################################

def check_for_updates(
    databaseBooking: Booking, 
    updatedBooking: Booking, 
    extractAllData: bool = True
) -> None:
    """
    Check for changes between original and updated bookings.
    
    Parameters:
        databaseBooking: Original booking from database
        updatedBooking: Updated booking with new values
        extractAllData: Whether all data should be checked for changes
        
    Returns:
        None
    """
    if not databaseBooking.emails.management:
        return
    
    if arrival_date_has_changed(databaseBooking, updatedBooking):
        return
    if departure_date_has_changed(databaseBooking, updatedBooking):
        return
    if not extractAllData:
        return

    if arrival_flight_has_changed(databaseBooking, updatedBooking):
        return
    if departure_flight_has_changed(databaseBooking, updatedBooking):
        return
    if arrival_time_has_changed(databaseBooking, updatedBooking):
        return
    if departure_time_has_changed(databaseBooking, updatedBooking):
        return
    if guest_numbers_have_changed(databaseBooking, updatedBooking):
        return
    if clean_has_changed(databaseBooking, updatedBooking):
        return

    cot_changes(databaseBooking, updatedBooking)
    high_chair_changes(databaseBooking, updatedBooking)
    mid_stay_clean_changes(databaseBooking, updatedBooking)
    late_checkout_changes(databaseBooking, updatedBooking)


def send_unmatched_row_email(worksheet: Worksheet) -> None:
    """
    Send an email notification about unmatched arrival/departure rows.
    
    Parameters:
        worksheet: Worksheet with the unmatched row
        
    Returns:
        None
    """
    subject = f'WARNING: Properties Sheets Issue: Unmatched arrival/departure rows in {worksheet.propertyName}'
    user, message = new_email(subject=subject, to='kevin@algarvebeachapartments.com', name='Dad')
    body = message.body
   
    body.paragraph('The updater found an issue on the properties sheet. See details here:')
    body.paragraph(f'Property: <b>{worksheet.propertyName}</b>')
    body.paragraph(f'Guest: <b>{worksheet.cell.value}</b>')
    body.paragraph(f'Row: <b>{worksheet.row.arrival}</b>')
    body.paragraph('Please check and modify accordingly.')
   
    send_email(user, message)
    return None