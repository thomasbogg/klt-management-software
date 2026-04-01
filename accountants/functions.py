from datetime import date

from apis.google.drives.file import GoogleDriveFile
from apis.google.mail.message import GoogleMailMessage
from default.accountancy.functions import (
    ACC_STORAGE_DIR,
    get_accountancy_sheet_bookings
)
from default.booking.booking import Booking
from default.database.database import Database
from default.google.mail.functions import new_email, send_email
from default.workbook.cells import (
    set_arrival_date_cell,
    set_booking_origin_cell,
    set_departure_date_cell,
    set_id_cell,
    set_internal_commission_cell,
    set_invoice_number_cell,
    set_invoice_total_cell,
    set_lead_guest_cell,
    set_management_fees_cell,
    set_nationality_cell,
    set_nif_cell,
    set_passport_cell,
    set_platform_fee_plus_iva_cell,
    set_total_rental_received_by_klt_cell,
    set_total_to_be_receipted_cell
)
from default.workbook.functions import (
    get_workbook as default_get_workbook,
    set_worksheet
)
from workbooks.workbook import Workbook
from workbooks.worksheet import Worksheet


DRIVE_FOLDER = 'Accountancy Sheets'


# Core utility functions
def get_workbook(filename: str) -> Workbook:
    """
    Get a workbook from the accountancy storage directory.
    
    Args:
        filename: Name of the workbook file
    
    Returns:
        The loaded workbook object
    """
    return default_get_workbook(filename, ACC_STORAGE_DIR)


def args_for_drive(filename: str, driveSubfolder: str) -> dict[str, str]:
    """
    Create arguments dictionary for drive operations.
    
    Args:
        filename: Name of the file
        driveSubfolder: Subfolder within the drive
    
    Returns:
        Dictionary with drive operation arguments
    """
    return {
        'drivePath': f'{DRIVE_FOLDER}/{driveSubfolder}',
        'filename': filename,
        'localDirectory': ACC_STORAGE_DIR,
        'backupFolderOnDrive': f'{DRIVE_FOLDER}'
    }


# Data retrieval functions
def get_accountants_sheet_bookings(
    database: Database, 
    start: date = None, 
    end: date = None, 
    noOwner: bool = True
) -> Database:
    """
    Get bookings data needed for accountants sheet.
    
    Args:
        database: Database instance
        start: Start date for filtering
        end: End date for filtering
        noOwner: Whether to exclude owner bookings
    
    Returns:
        Database search object with selections and conditions set
    """
    search = get_accountancy_sheet_bookings(database, start, end, noOwner)
    
    # Select details data
    select = search.details.select()
    select.adults()
    select.children()
    select.babies()

    # Select arrival data
    select = search.arrivals.select()
    select.meetGreet()

    # Select departures data
    select = search.departures.select()
    select.clean()
    
    # Select charges data
    select = search.charges.select()
    select.admin()

    # Select extras data for management fee costing
    select = search.extras.select()
    select.all()
    
    # Select property specs data
    select = search.propertySpecs.select()
    select.bedrooms()

    # Select property owners data
    select = search.propertyOwners.select()
    select.cleansAreInvoiced()

    return search


# Cell configuration functions
def cells(
    id: bool = True, 
    management: bool = True, 
    splitPayments: bool = False
) -> tuple[callable, ...]:
    """
    Get a tuple of cell setter functions for accountancy worksheets.
    
    Args:
        id: Whether to include ID cell setter
        management: Whether to include management fees cell setter
        splitPayments: Whether to use split payment cell setters
    
    Returns:
        Tuple of cell setter functions
    """
    cellSetters = [
        set_id_cell,
        set_lead_guest_cell,
        set_booking_origin_cell,
        set_arrival_date_cell,
        set_departure_date_cell,
        set_passport_cell,
        set_nif_cell,
        set_nationality_cell,
        set_total_to_be_receipted_cell,
        set_platform_fee_plus_iva_cell,
        set_total_rental_received_by_klt_cell,
        set_internal_commission_cell,
        set_management_fees_cell,
        set_invoice_number_cell,
        set_invoice_total_cell,
    ]
    
    if not id:
        cellSetters.remove(set_id_cell)
 
    if not management:
        cellSetters.remove(set_management_fees_cell)
 
    if splitPayments:
        commisionIndex = cellSetters.index(set_internal_commission_cell)
        cellSetters[commisionIndex] = set_split_internal_commission_cell
        platformFeeIndex = cellSetters.index(set_platform_fee_plus_iva_cell)
        cellSetters[platformFeeIndex] = set_split_platform_fee_plus_iva_cell
        managementFeesIndex = cellSetters.index(set_management_fees_cell)
        cellSetters[managementFeesIndex] = set_split_management_fees_cell
        invoiceNumberIndex = cellSetters.index(set_invoice_number_cell)
        cellSetters[invoiceNumberIndex] = set_split_invoice_number_cell
        invoiceTotalIndex = cellSetters.index(set_invoice_total_cell)
        cellSetters[invoiceTotalIndex] = set_split_invoice_total_cell
 
    return tuple(cellSetters)


# Worksheet configuration functions
def set_split_payments_worksheet(
    name: str, 
    start: date = None, 
    end: date = None, 
    checkExchange: bool = False, 
    checkHide: bool = False, 
    owners: tuple[str, ...] = tuple(), 
    fractions: tuple[float, ...] = tuple()
) -> Worksheet:
    """
    Set up the worksheet for split payments.
    
    Args:
        name: Worksheet name
        start: Start date for worksheet
        end: End date for worksheet
        checkExchange: Whether to check exchange rates
        checkHide: Whether to hide certain elements
        owners: Tuple of owner names
        fractions: Tuple of payment fractions corresponding to owners
    
    Returns:
        A new worksheet instance with split payments recipients and fractions set up
    """
    worksheet = set_worksheet(name, start, end, checkExchange=checkExchange, checkHide=checkHide)
    worksheet.names = owners
    worksheet.fractions = fractions
    return worksheet


# Split payment cell setter functions
def set_split_platform_fee_plus_iva_cell(
    worksheet: Worksheet, 
    booking: Booking | None, 
    **kwargs
) -> Worksheet:
    """
    Set the platform fee plus IVA cell with split payment formatting.
    
    Args:
        worksheet: The worksheet to update
        booking: The booking containing fee data
        **kwargs: Additional arguments for cell formatting
    
    Returns:
        The updated worksheet
    """
    return set_platform_fee_plus_iva_cell(
        worksheet, 
        booking, 
        split=True, 
        dataFormat=worksheet.cell._euros_format(), 
        **kwargs
    )


def set_split_internal_commission_cell(
    worksheet: Worksheet, 
    booking: Booking | None, 
    **kwargs
) -> Worksheet:
    """
    Set the internal commission cell with split payment formatting.
    
    Args:
        worksheet: The worksheet to update
        booking: The booking containing commission data
        **kwargs: Additional arguments for cell formatting
    
    Returns:
        The updated worksheet
    """
    return set_internal_commission_cell(
        worksheet, 
        booking, 
        split=True, 
        dataFormat=worksheet.cell._euros_format(), 
        **kwargs
    )


def set_split_management_fees_cell(
    worksheet: Worksheet, 
    booking: Booking | None, 
    **kwargs
) -> Worksheet:
    """
    Set the management fees cell with split payment formatting.
    
    Args:
        worksheet: The worksheet to update
        booking: The booking containing fee data
        **kwargs: Additional arguments for cell formatting
    
    Returns:
        The updated worksheet
    """
    return set_management_fees_cell(
        worksheet, 
        booking, 
        split=True, 
        dataFormat=worksheet.cell._euros_format(), 
        **kwargs
    )


def set_split_invoice_total_cell(
    worksheet: Worksheet, 
    booking: Booking | None, 
    **kwargs
) -> Worksheet:
    """
    Set the invoice total cell with split payment formatting.
    
    Args:
        worksheet: The worksheet to update
        booking: The booking containing invoice data
        **kwargs: Additional arguments for cell formatting
    
    Returns:
        The updated worksheet
    """
    return set_invoice_total_cell(
        worksheet, 
        booking, 
        split=True, 
        dataFormat=worksheet.cell._euros_format(), 
        **kwargs
    )


def set_split_invoice_number_cell(
    worksheet: Worksheet, 
    *args, 
    **kwargs
) -> Worksheet:
    """
    Set the invoice number cell with split payment formatting.
    
    Args:
        worksheet: The worksheet to update
        *args: Variable positional arguments
        **kwargs: Additional arguments for cell formatting
    
    Returns:
        The updated worksheet
    """
    return set_invoice_number_cell(worksheet, split=True, **kwargs)


# Permission functions
def create_permissions(
    driveFile: GoogleDriveFile, 
    accountantEmail: str = None, 
) -> None:
    """
    Create permissions for the accountant on the Google Drive file.
    
    Args:
        driveFile: The Google Drive file to set permissions on
        accountantEmail: Email address of the accountant
    """
    permissions = driveFile.permissions
    if accountantEmail:
        permissions.emailAddress = accountantEmail
    permissions.role = 'reader'
    permissions.type = 'user'
    permissions.create()


# Email functions
def send_new_email_to_accountant(
    accountantEmail: str, 
    accountantName: str, 
    propertyName: str, 
    driveFile: GoogleDriveFile, 
    date: date
) -> None:
    """
    Create and send an email to the accountant with workbook details.
    
    Composes an email with a link to the updated workbook and sends it
    to the accountant, with a copy to Kevin.
    
    Args:
        accountantEmail: Email address of the accountant
        accountantName: Name of the accountant
        propertyName: Name of the property in the workbook
        driveFile: Google Drive file to link in the email
        date: Date for email subject line
    """
    subject = f'Accountancy Report for {propertyName} - {date.year}.'
    user, message = new_email(to=accountantEmail, subject=subject, name=accountantName)
    message.cc = 'kevin@algarvebeachapartments.com'
    body = message.body
    opening(body, propertyName)
    link(body, driveFile.link)
    closing(body)
    send_email(user, message, checkSent=True)


def opening(body: GoogleMailMessage.Body, propertyName: str) -> None:
    """
    Add opening paragraph to email body.
    
    Args:
        body: Email body to add text to
        propertyName: Name of the property to mention
    """
    body.paragraph(
        f'There has been an update to the accountancy report for {propertyName}.',
        'If the latest Invoice Numbers are not yet present in the specified column,',
        'our internal finance manager will add them shortly.'
    )


def link(body: GoogleMailMessage.Body, link: str) -> None:
    """
    Add a hyperlink to the email body.
    
    Args:
        body: Email body to add link to
        link: URL to link to
    """
    body.link(
        link,
        'See the updated Accountancy Report here.'
    )


def closing(body: GoogleMailMessage.Body) -> None:
    """
    Add closing paragraph to email body.
    
    Args:
        body: Email body to add text to
    """
    body.paragraph(
        'I trust this has been helpful. As always, I remain available for questions.'
    )