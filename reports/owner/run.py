from datetime import date

from accountants.functions import get_accountants_sheet_bookings
from apis.google.mail.message import GoogleMailMessage
from correspondence.owner.functions import new_owner_email
from default.booking.booking import Booking
from default.booking.functions import (
    determine_management_fee,
    determine_owner_balance, 
    determine_owner_payment, 
    hideCharges
)
from default.database.database import Database
from default.database.functions import (
    get_database, 
    search_properties, 
    set_property_name
)
from default.dates import dates
from default.google.drive.functions import (
    download_drive_file_to_local_storage, 
    upload_local_file_to_drive
)
from default.property.property import Property
from default.settings import GBP_EUR_EXCHANGE_RATE
from default.update.dates import updatedates
from default.update.wrapper import update
from default.workbook.cells import (
    is_header,
    set_arrival_date_cell,
    set_basic_holiday_charge_cell,
    set_booking_origin_cell,
    set_cell,
    set_currency_used_by_guest_cell,
    set_departure_date_cell,
    set_header_cell,
    set_id_cell,
    set_internal_commission_cell,
    set_lead_guest_cell,
    set_management_fees_cell,
    set_nationality_cell,
    set_nif_cell,
    set_passport_cell,
    set_platform_fee_cell,
    set_platform_fee_iva_cell,
    set_rental_to_owner_cell,
    set_total_guests_cell,
    set_total_nights_cell,
    set_total_to_be_receipted_cell,
)
from default.workbook.functions import (
    create_worksheet, 
    determine_years_order, 
    get_workbook, 
    set_worksheet, 
    update_worksheet
)
from utils import log, sublog
from workbooks.dates import WorksheetDates
from workbooks.worksheet import Worksheet


# Constants
DRIVE_FOLDER = 'Bookings Reports'
LOCAL_STORAGE_DIR = 'bookings-reports'


@update
def update_bookings_reports_workbooks(
    start: date = None, 
    end: date = None, 
    propertyName: str = None, 
    sendEmail: bool = True,
    reset: bool = False
) -> str:
    """
    Update booking reports workbooks for property owners.
    
    Creates or updates Excel workbooks showing booking information for each property
    and optionally emails the reports to the respective property owners.
    
    Args:
        start: The start date for bookings to include. If None, uses default owner dates.
        end: The end date for bookings to include. If None, uses default owner dates.
        propertyName: Optional property name to filter for a specific property.
        sendEmail: Whether to email reports to property owners after updating.
        
    Returns:
        A string indicating successful completion.
    """
    if start is None and end is None: 
        start, end = updatedates.owner_reports_update_dates()
    
    properties = _get_properties()
    database = get_database()

    for property in properties:
        if propertyName and propertyName not in (property.name, property.shortName): 
            continue

        filename = f'{property.name}, Bookings Report.xlsx'
        log(f'DOING: {filename}')
        workbook = get_workbook(filename, LOCAL_STORAGE_DIR)
        driveFile = download_drive_file_to_local_storage(**_args_for_drive(filename))
        workbook.load() if driveFile else workbook.create()

        datesByYears = dates.breakDatesByYears(start=start, end=end)
        for currentStart, currentEnd in datesByYears:
            if property.shortName == 'A26' and currentStart.year < 2025: 
                continue
        
            sublog(f'editing for dates: {currentStart} TO {currentEnd}')
            bookings = _get_bookings(
                                    database, 
                                    currentStart,
                                    currentEnd, 
                                    property.shortName)
            sheet = set_worksheet(
                                str(currentStart.year), 
                                currentStart, 
                                currentEnd, 
                                checkExchange=True, 
                                checkHide=True, 
                                stringDates=True)
            if workbook.hasSheet(sheet): 
                if reset:
                    workbook.deleteSheet(sheet)
                    create_worksheet(workbook.newSheet(sheet), bookings, _cells(property))
                else:
                    update_worksheet(workbook.getSheet(sheet), bookings, _cells(property), startEndCol=4)
            else: 
                create_worksheet(workbook.newSheet(sheet), bookings, _cells(property))
        
        workbook.orderSheets(determine_years_order(workbook.sheetnames)).save()
        driveFile = upload_local_file_to_drive(driveFile, **_args_for_drive(filename))

        if sendEmail:
            sublog('report updated, now sending to owner!')
            _new_bookings_reports_email_to_owner(property, driveFile.path)
    
    database.close()
    return 'Successfully updated Bookings Reports workbooks!'


def _args_for_drive(filename: str) -> dict[str, str]:
    """
    Generate arguments for Google Drive operations.
    
    Args:
        filename: The name of the file to operate on.
        
    Returns:
        A dictionary with the necessary arguments for Drive operations.
    """
    return {
        'drivePath': DRIVE_FOLDER,
        'filename': filename,
        'localDirectory': LOCAL_STORAGE_DIR,
        'backupFolderOnDrive': DRIVE_FOLDER,
    }


def _get_properties() -> list[Property]:
    """
    Retrieve properties that we book and manage.
    
    Returns:
        A list of Property objects that we book.
    """
    search = search_properties()

    select = search.properties.select()
    select.weClean()
    select.accountantId()

    select = search.propertyOwners.select()
    select.name()
    select.email()
    select.takesEuros()
    select.takesPounds()
    select.isPaidRegularly()

    where = search.properties.where()
    where.weBook().isTrue()

    return search.fetchall()


def _get_bookings(database: Database, start: date, end: date, 
                  propertyName: str = None) -> list[Booking]:
    """
    Get bookings data needed for owner reports.
    
    Args:
        database: Database instance to query.
        start: Start date for filtering bookings.
        end: End date for filtering bookings.
        propertyName: Property name for filtering bookings.
        
    Returns:
        A list of Booking objects matching the criteria.
    """
    search = get_accountants_sheet_bookings(database, start, end, noOwner=False)
    
    select = search.details.select()
    select.adults()
    select.children()
    select.babies()
    select.isOwner()
    
    select = search.arrivals.select()
    select.meetGreet()

    select = search.departures.select()
    select.clean()

    select = search.charges.select()
    select.admin()

    select = search.propertySpecs.select()
    select.bedrooms()

    set_property_name(search, propertyName)

    where = search.details.where()
    where.enquirySource().isNotEqualTo('KKLJ')

    return search.fetchall()


def _cells(property: Property) -> tuple:
    """
    Get the appropriate cell setter functions for a property's report.
    
    Creates a custom list of cell setter functions based on property characteristics,
    such as whether the owner takes both currencies, is paid regularly, or if we clean.
    
    Args:
        property: The property to determine cell setters for.
        
    Returns:
        A tuple of cell setter functions to use for the worksheet.
    """
    cells = [
        set_id_cell,
        set_lead_guest_cell,
        set_booking_origin_cell,
        set_arrival_date_cell,
        set_departure_date_cell,
        set_total_guests_cell,
        set_total_nights_cell,
    ]
 
    if property.shortName != '39-2B':
        cells.extend([
            set_passport_cell,
            set_nif_cell,
            set_nationality_cell
        ])

    if property.owner.takesBothCurrencies:
        cells.append(set_currency_used_by_guest_cell)

    if property.accountantId is None:
        cells.append(_set_total_to_be_receipted_cell)

    cells.extend([
        set_platform_fee_cell,
        set_platform_fee_iva_cell,
        set_basic_holiday_charge_cell,
        set_internal_commission_cell,
    ])

    if property.owner.isPaidRegularly:
        cells.extend([
            set_rental_due_to_owner_cell,
            set_rental_paid_to_owner_cell,
            set_date_of_payment_cell,
        ])
    else:
        cells.append(set_rental_to_owner_cell)

    if property.weClean:
        cells.extend([
            set_management_fees_cell,
            set_estimated_net_revenue_cell,
            set_running_estimated_net_revenue_cell,
        ])

    return tuple(cells)


def _set_total_to_be_receipted_cell(worksheet: Worksheet, booking: Booking | None,
                                    **kwargs) -> Worksheet:
    """
    Set a cell with the total rental to be receipted.
    Checks whether the column exists before updating the sheet.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking containing rental information, or None for header row.
        **kwargs: Additional arguments passed to set_cell.
        
    Returns:
        The modified worksheet.
    """
    columnName = 'Total to be Receipted'
    
    if not is_header(worksheet) and columnName not in worksheet.columnNames:
        savedRowCount = worksheet.row.count
        worksheet.row.count = worksheet.row.firstDataRow - 1
        worksheet.column.insert()
        worksheet.columnNames.append(columnName)
        set_total_to_be_receipted_cell(worksheet, booking=None)
        worksheet.row.count = savedRowCount
   
    if booking:
        if not booking.details.isPlatform or _is_before_new_VAT_law(booking):
            booking = None
    return set_total_to_be_receipted_cell(worksheet, booking=booking, **kwargs)


def set_rental_due_to_owner_cell(worksheet: Worksheet, booking: Booking | None, 
                                **kwargs) -> Worksheet:
    """
    Set a cell with the rental amount due to owner.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking containing rental information, or None for header row.
        **kwargs: Additional arguments passed to set_cell.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Rental Due to Owner', width=10, **kwargs)
    
    if booking:
        worksheet.cell.setToCurrencyFormat(booking.charges.currency)
        value: float | str = _determine_rental_due_to_owner(booking)
    else:
        value: None = None
    return set_cell(worksheet, value=value, **kwargs)


def set_rental_paid_to_owner_cell(worksheet: Worksheet, booking: Booking | None, 
                                 **kwargs) -> Worksheet:
    """
    Set a cell with the rental amount paid to owner.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking containing rental information, or None for header row.
        **kwargs: Additional arguments passed to set_cell.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Rental Paid to Owner', width=10, **kwargs)
    
    if booking:
        worksheet.cell.setToCurrencyFormat(booking.charges.currency)
        value: float | str = _determine_rental_paid_to_owner(booking)
    else:
        value: None = None
    return set_cell(worksheet, value=value, **kwargs)


def set_date_of_payment_cell(worksheet: Worksheet, booking: Booking | None, 
                            **kwargs) -> Worksheet:
    """
    Set a cell with the date of payment to owner.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking containing payment information, or None for header row.
        **kwargs: Additional arguments passed to set_cell.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Date of Payment', width=9, **kwargs)
    
    if booking:
        onwerPaymentDate = _determine_owner_payment_date(booking)
        if onwerPaymentDate == '-':
            value: str = '-'
        else:
            worksheet.cell.setToDateFormat()
            value: str = WorksheetDates.toStringDate(onwerPaymentDate)
    else:
        value: None = None    
    return set_cell(worksheet, value=value, **kwargs)


def set_estimated_net_revenue_cell(worksheet: Worksheet, booking: Booking | None, 
                                  **kwargs) -> Worksheet:
    """
    Set a cell with the estimated net revenue for the owner.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking containing revenue information, or None for header row.
        **kwargs: Additional arguments passed to set_cell.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, 
                              value='Est. Net Revenue after All Std. Deductions', 
                              width=18, **kwargs)
    
    worksheet.cell.setToEurosFormat()
    if booking:
        value: float | str = _determine_owner_net_revenue(booking)
    else:
        value: None = None
    return set_cell(worksheet, value=value, **kwargs)


def set_running_estimated_net_revenue_cell(worksheet: Worksheet, booking: Booking | None, 
                                          **kwargs) -> Worksheet:
    """
    Set a cell with running total of estimated net revenue.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking containing revenue information, or None for header row.
        **kwargs: Additional arguments passed to set_cell.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, 
                              value='Est. Running Net Rev. after All Std. Deductions', 
                              width=18, **kwargs)
    
    worksheet.cell.setToEurosFormat()
    worksheet.cell.setRunningTotal()
    return set_cell(worksheet, **kwargs)


@hideCharges
def _determine_owner_net_revenue(booking: Booking) -> float:
    """
    Calculate the net revenue after all standard deductions for a given booking.
    
    Args:
        booking: The booking object containing relevant information.
        
    Returns:
        The calculated net revenue.
    """
    if booking.charges.applyExchangeRate or booking.charges.currency == 'EUR':
        return determine_owner_balance(booking)
    return (
        determine_owner_payment(booking) * 
        GBP_EUR_EXCHANGE_RATE - 
        determine_management_fee(booking)
    )


def _determine_owner_payment_date(booking: Booking) -> date:
    """
    Get the date of payment to the owner for a given booking.
    
    Args:
        booking: The booking object containing relevant information.
        
    Returns:
        The date of payment to the owner (2 days after arrival).
    """
    if booking.details.isOwner:
        return '-'
    return dates.calculate(date=booking.arrival.date, days=2)


@hideCharges
def _determine_rental_due_to_owner(booking: Booking) -> float:
    """
    Calculate the rental amount due to the owner for a given booking.
    
    Args:
        booking: The booking object containing relevant information.
        
    Returns:
        The calculated rental amount due to the owner or 0 if already paid.
    """
    ownerPaymentDate = _determine_owner_payment_date(booking)
    if ownerPaymentDate == '-' or dates.date() >= ownerPaymentDate:
        return 0.0
    return determine_owner_payment(booking)
    
    
@hideCharges
def _determine_rental_paid_to_owner(booking: Booking) -> float:
    """
    Calculate the rental amount paid to the owner for a given booking.
    
    Args:
        booking: The booking object containing relevant information.
        
    Returns:
        The calculated rental amount paid to the owner or 0 if not yet paid.
    """
    ownerPaymentDate = _determine_owner_payment_date(booking)
    if ownerPaymentDate == '-' or dates.date() < ownerPaymentDate:
        return 0.0
    return determine_owner_payment(booking)


def _is_before_new_VAT_law(booking: Booking) -> bool:
    """
    Checks whether the arrival date is prior to new PT VAT law.
    
    Args:
        booking: The booking object containing arrival info.
        
    Returns:
        The bool value of the cut-off date.
    """
    return booking.arrival.date < dates.date(2025, 7, 1)


def _new_bookings_reports_email_to_owner(property: Property, filePaths: str) -> None:
    """
    Create and send an email to the property owner with the booking report.
    
    Args:
        property: The property object containing owner info.
        filePaths: Path to the report file to attach.
        
    Returns:
        None
    """
    subject = f'Bookings Report Update for {property.name}'
    user, message = new_owner_email(property=property, subject=subject)
    message.attachments = filePaths
    body = message.body
    _salutation(body)
    _introduction(body)
    _howto(body)
    if property.accountantId is None:
        _accountancy_column_note(body)
    _conclusion(body)
    from default.google.mail.functions import send_email
    send_email(user, message, checkSent=True)
    return None
    

def _salutation(body: GoogleMailMessage.Body) -> None:
    """
    Add salutation to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'I hope this finds you well.'
    )


def _introduction(body: GoogleMailMessage.Body) -> None:
    """
    Add introduction paragraph to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'I am sending the latest update on bookings for your property. Please',
        'find the report attached.',
    )

        
def _howto(body: GoogleMailMessage.Body) -> None:
    """
    Add instructions for opening the report to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'Some have mentioned <u>difficulty reading the report</u>. This is an',
        '"xlsx" file which is best read using Google Sheets, Microsoft Excel, or',
        'LibreOffice Calc. Thus, I recommend either saving it to Google Drive',
        'and then opening it with Google Sheets or downloading the file onto your',
        'desktop computer and opening it with Microsoft Excel or LibreOffice Calc.'
    )

        
def _accountancy_column_note(body: GoogleMailMessage.Body) -> None:
    """
    Add notice of the accountancy column for invoicing/receipting.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'You will now find an additional column in the reports called "Total to be',
        'receipted". This is for the purposes of reporting to your accountant the',
        'total amount that must be invoiced for the stay. It only applies to platform',
        'bookings that take place after 1 July 2025 for the start of the new VAT regime.',
        'For bookings that do not meet this criteria, you will see a €0.00 value.'
    )


def _conclusion(body: GoogleMailMessage.Body) -> None:
    """
    Add conclusion to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'I trust that this has been helpful. If you have any questions, I am always',
        'available. Please feel free to reach out.'
    )