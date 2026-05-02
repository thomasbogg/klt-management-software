from correspondence.self.functions import new_email_to_self, send_email_to_self
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import (
    get_database, 
    search_bookings, 
    set_valid_management_booking
)
from default.google.drive.functions import (
    download_drive_file_to_local_storage,
    upload_local_file_to_drive
)
from default.update.dates import updatedates
from default.update.wrapper import update
from default.workbook.cells import (
    is_header,
    set_arrival_date_cell,
    set_cell, 
    set_departure_date_cell,
    set_header_cell, 
    set_id_cell as default_set_id_cell,
    set_lead_guest_cell,
    set_property_cell
)
from default.workbook.functions import (
    cells_are_empty,
    create_worksheet,
    get_workbook,
    insert_bookings,
    set_worksheet
)
from typing import Callable
from workbooks.worksheet import Worksheet


# Main update function
@update
def update_bookingCom_guest_contacts(start: str | None = None, end: str | None = None) -> str:
    """
    Update Booking.com guest contact information for a date range.
    
    Args:
        start: Start date for the update. If None, uses default dates.
        end: End date for the update. If None, uses default dates.
        
    Returns:
        String describing the result of the update operation.
    """
    if start is None and end is None: 
        start, end = updatedates.bookingCom_guest_contacts_dates()
    
    database = get_database()
    bookings = get_upcoming_booking_com_bookings(database, start, end)
    if not bookings:
        return f'GOT NO new guests to update on dates {start} to {end}...'

    fileName = 'BookingCom Guest Details Updater.xlsx'
    driveFile = download_drive_file_to_local_storage(**args_for_drive(fileName))
    workbook = get_workbook(fileName, 'guest-management')
    workbook.load() if driveFile else workbook.create()

    sheet = set_worksheet('Guests')
    if not workbook.hasSheet(sheet):
        create_worksheet(workbook.insertSheet(sheet), bookings, cells())
        newEntries = True
    else:
        sheet.row.number = sheet.row.firstDataRow
        newEntries = update_worksheet(workbook.openSheet(sheet), bookings)
    
    workbook.save()
    driveFile = upload_local_file_to_drive(driveFile, **args_for_drive(fileName))

    if newEntries:
        user, message = new_email_to_self(subject='Missing Contact Details for BOOKING.COM Guests')
        message.body.link(driveFile.link, 'Update Guests Here')
        send_email_to_self(user, message)

    database.close()
    return 'Successfully updated and uploaded BookingCom Guest Details Workbook'


# Drive-related functions
def args_for_drive(filename: str) -> dict[str, str]:
    """
    Get arguments for Google Drive operations.
    
    Args:
        filename: Name of the file to use in Google Drive.
        
    Returns:
        Dictionary containing drive path, filename, and local directory.
    """
    return {
        'drivePath': 'Guest Management',
        'filename': filename,
        'localDirectory': 'guest-management',
    }


# Booking-related functions
def get_booking_com_link(booking: Booking) -> str:
    """
    Generate a link to the Booking.com extranet for a specific booking.
    
    Args:
        booking: The booking object to generate a link for.
        
    Returns:
        URL string for the booking in Booking.com extranet.
    """
    platId = booking.details.platformId.split('-')[0]
    propId = booking.property.bookingComId
    return (
        'https://admin.booking.com/hotel/hoteladmin/'
        'extranet_ng/manage/booking.html?hotel_id='
        f'{propId}&lang=en&res_id={platId}'
    )


def get_upcoming_booking_com_bookings(database: Database, start: str, end: str) -> list[Booking]:
    """
    Get all upcoming bookings from Booking.com with missing contact information.
    
    Args:
        database: Database connection to use for queries.
        start: Start date for booking search.
        end: End date for booking search.
        
    Returns:
        List of Booking objects from Booking.com with missing contact information.
    """
    search = search_bookings(database, start, end)
    select = search.guests.select()
    select.id()
    select.firstName()
    select.lastName()

    select = search.details.select()
    select.platformId()

    select = search.arrivals.select()
    select.date()

    select = search.departures.select()
    select.date()

    select = search.properties.select()
    select.name()
    select.shortName()

    where = search.guests.where()
    where.email().isNullEmptyOrFalse()

    where = search.details.where()
    where.enquirySource().isEqualTo('Booking.com')
    where.isOwner().isFalse()

    set_valid_management_booking(search)
    return search.fetchall()


# Worksheet operations
def update_worksheet(worksheet: Worksheet, bookings: list[Booking]) -> bool:
    """
    Update the worksheet with booking information and process existing entries.
    
    Args:
        worksheet: Worksheet to update.
        bookings: List of bookings to add to the worksheet.
        
    Returns:
        True if new entries were added, False otherwise.
    """
    row = worksheet.row
    if cells_are_empty(worksheet, (1,)):
        if bookings:
            insert_bookings(worksheet, bookings, cells())
            return True
        return False
   
    column = worksheet.column
    column.number = 1
    guestId = worksheet.cell.value
    column.number = 6
    guestEmail = worksheet.cell.value
    column.number = 7
    guestPhone = worksheet.cell.value
   
    if guestEmail and len(guestEmail) > 10:
        booking: Booking = list(filter(lambda b: b.guest.id == guestId, bookings))[0]
        booking.guest.email = guestEmail
        booking.guest.phone = guestPhone.split(':')[-1]
        booking.update()
        bookings.remove(booking)
   
    row.delete()
    return update_worksheet(worksheet, bookings)


# Cell setting functions
def set_id_cell(worksheet: Worksheet, booking: Booking | None = None) -> Worksheet:
    """
    Set the ID cell for the booking.
    
    Args:
        worksheet: Worksheet to modify.
        booking: Booking object to extract ID from, or None for header row.
        
    Returns:
        Modified worksheet.
    """
    if is_header(worksheet):
        return default_set_id_cell(worksheet, None)
    
    if booking:
        worksheet.cell.setToNumberFormat()
        return set_cell(worksheet, value=booking.guest.id)
    
    return set_cell(worksheet)


def set_platform_link_cell(worksheet: Worksheet, booking: Booking | None = None) -> Worksheet:
    """
    Set the platform link cell for the booking.
    
    Args:
        worksheet: Worksheet to modify.
        booking: Booking object to extract platform link from, or None for header row.
        
    Returns:
        Modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, width=12, value='Platform LINK')
    
    if booking:
        worksheet.cell.setToTextFormat()
        return set_cell(worksheet, value='CLICK', hyperlink=get_booking_com_link(booking))
    
    return set_cell(worksheet)


def set_guest_email_cell(worksheet: Worksheet, booking: Booking | None = None) -> Worksheet:
    """
    Set the guest email cell for the booking.
    
    Args:
        worksheet: Worksheet to modify.
        booking: Booking object (unused), or None for header row.
        
    Returns:
        Modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, width=30, value='Guest Email')
    return set_cell(worksheet)


def set_guest_phone_cell(worksheet: Worksheet, booking: Booking | None = None) -> Worksheet:
    """
    Set the guest phone cell for the booking.
    
    Args:
        worksheet: Worksheet to modify.
        booking: Booking object (unused), or None for header row.
        
    Returns:
        Modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, width=25, value='Guest Phone')
    return set_cell(worksheet)


def cells() -> tuple[Callable[[Worksheet, Booking | None], Worksheet], ...]:
    """
    Return the cell setter functions for the Booking.com guest details worksheet.
    
    Returns:
        Tuple of cell setter functions in the order they should be applied.
    """
    return (
        set_id_cell,
        set_lead_guest_cell,
        set_arrival_date_cell,
        set_departure_date_cell,
        set_property_cell,
        set_guest_email_cell,
        set_guest_phone_cell,
        set_platform_link_cell,
    )