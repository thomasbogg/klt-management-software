from datetime import date, datetime
from default.booking.booking import Booking
from default.booking.functions import logbooking
from default.database.database import Database
from default.database.functions import search_bookings, search_properties
from default.dates import dates
from default.property.property import Property
from default.workbook.functions import (
    cells_are_empty,
    get_workbook as default_get_workbook,
    id_not_in_bookings,
    row_date_is_after_end_date,
    row_date_is_before_start_date
)
from sheets.cells import (
    set_additional_cell,
    set_basic_cell,
    set_clean_cell,
    set_column_headers,
    set_contact_cell,
    set_cost_cell,
    set_date_cell,
    set_details_cell,
    set_extras_cell,
    set_group_cell,
    set_id_cell,
    set_lead_guest_cell,
    set_meet_greet_cell,
    set_observations_cell,
    set_property_header,
    set_run_tot_cell,
    set_time_cell
)
from workbooks.stylesheet import Stylesheet
from workbooks.worksheet import Worksheet
from workbooks.workbook import Workbook


#######################################################
# CONSTANTS
#######################################################

LOCAL_DIR = 'properties-sheets'
DRIVE_DIR = 'Properties Sheets'


#######################################################
# WORKBOOK AND FILENAME FUNCTIONS
#######################################################

def get_workbook(filename: str) -> Workbook:
    """
    Get a workbook by filename from the local directory.
    
    Parameters:
        filename: The name of the workbook file
        
    Returns:
        The requested Workbook object
    """
    return default_get_workbook(filename, LOCAL_DIR)


def get_filename(owner: str | None = None, properties: list[Property] | None = None) -> str:
    """
    Generate a filename for a property sheet based on owner and properties.
    
    Parameters:
        owner: Owner name to include in the filename
        properties: List of properties to include in the filename
        
    Returns:
        Generated filename string
    """
    return f'{", ".join([property.shortName for property in properties])} - {owner}.xlsx'


def args_for_drive(filename: str) -> dict[str, str]:
    """
    Create arguments dictionary for Google Drive operations.
    
    Parameters:
        filename: The name of the file to operate on
        
    Returns:
        Dictionary with drive operation parameters
    """
    return {
        'drivePath': DRIVE_DIR,
        'filename': filename,
        'localDirectory': LOCAL_DIR,
        'backupFolderOnDrive': DRIVE_DIR
    }


#######################################################
# WORKSHEET SETUP AND CREATION
#######################################################

def set_worksheet(name: str, start: date | int | None = None, end: date | int | None = None) -> Worksheet:
    """
    Create and configure a worksheet with specified settings.
    
    Parameters:
        name: Name of the worksheet
        start: Start date or row number
        end: Optional end date or row number
        
    Returns:
        Configured worksheet object
    """
    worksheet = Worksheet(name)
    worksheet.start = start
    worksheet.end = end
    worksheet.currentBorderRow = None
    worksheet.latestBorderRow = None

    row = worksheet.row
    row.firstDataRow = 9
    row.maxEmptiesAllowed = 15
    row.defaultHeight = 20
    row.defaultDelete = 3
    row.defaultInsert = 3
    
    column = worksheet.column
    column.firstDataColumn = 1
    return worksheet


def create_worksheet(worksheet: Worksheet, property: Property) -> Worksheet:
    """
    Create a new property worksheet with headers and formatting.
    
    Parameters:
        worksheet: The worksheet to configure
        property: The property to create the sheet for
        
    Returns:
        The configured worksheet
    """
    set_property_header(worksheet, property)
    set_column_headers(worksheet)
    row = worksheet.row
    row.freeze(row.firstDataRow)
    return worksheet


#######################################################
# WORKSHEET UPDATE FUNCTIONS
#######################################################

def update_worksheet(
    workbook: Workbook, 
    worksheet: Worksheet, 
    bookings: list[Booking], 
    property: Property, 
    skipFirstRow: bool = False
) -> bool:
    """
    Update a worksheet with booking data.
    
    Parameters:
        worksheet: The worksheet to update
        bookings: List of bookings to add to the worksheet
        
    Returns:
        True if a new sheet was created, False otherwise
    """
    worksheet.row.number = worksheet.row.firstDataRow - 1
    worksheet, lastRowNumber = _update_worksheet(
        worksheet,
        bookings,
        skipFirstRow=skipFirstRow
    )

    if lastRowNumber > 180:
        firstDateTaken, lastDateTaken = create_new_sheet_for_property(workbook, worksheet, property, lastRowNumber)
        return firstDateTaken, lastDateTaken
    
    set_latest_date_border(worksheet)
    return False


def _update_worksheet(
    worksheet: Worksheet, 
    bookings: list[Booking], 
    skipFirstRow: bool = False
) -> Worksheet:
    """
    Recursively update a worksheet by processing rows and inserting bookings.
    
    Parameters:
        worksheet: The worksheet to update
        bookings: List of bookings to add to the worksheet
        skipFirstRow: Whether to skip the first row
        
    Returns:
        The updated worksheet
    
    This function processes rows recursively, checking conditions such as 
    empty cells, row dates, and booking IDs to determine the appropriate 
    action (insert, delete, or skip rows). Bookings are inserted sequentially
    from the provided list, and the list is modified in-place.
    """
    row = worksheet.row
    if row.atMaxEmpties:
        return worksheet, row.number

    row.increase()
    row.setHeight()

    if skipFirstRow and row.number == worksheet.row.firstDataRow:
        return _update_worksheet(worksheet, bookings)

    skip_departure_rows(worksheet)

    if cells_are_empty(worksheet, (1,)):
        row.increaseEmptyCount()
       
        if not cells_are_empty(worksheet, (17,)):
            row.resetEmptyCount()

        if bookings and row.emptiesCount == 3:
            row.decrease()
            booking = bookings.pop(0)
            logbooking(booking, inline='NEW booking:')
        else:
            booking = None
    
        insert_in_row(worksheet, booking)
        return _update_worksheet(worksheet, bookings)

    row.resetEmptyCount()

    if row_date_is_before_start_date(worksheet, 2):
        return _update_worksheet(worksheet, bookings)

    if row_date_is_after_end_date(worksheet, 2):
        if bookings:
            row.insert()
            booking = bookings.pop(0)
            logbooking(booking, inline='NEW booking:')
        else:
            booking = None
  
        insert_in_row(worksheet, booking)
        return _update_worksheet(worksheet, bookings)
    
    if bookings:
        booking = bookings[0]
        worksheet.column.number = worksheet.column.firstDataColumn
        rowId = worksheet.cell.value
    
        if booking.id != rowId:
            if id_not_in_bookings(bookings, rowId):
                row.delete()
                row.decrease()
                return _update_worksheet(worksheet, bookings)
    
            row.insert()
            logbooking(booking, inline='NEW booking:')
    
        booking = bookings.pop(0)
        insert_in_row(worksheet, booking)
        return _update_worksheet(worksheet, bookings)
    
    row.delete()
    row.decrease()
    return _update_worksheet(worksheet, bookings)


#######################################################
# ROW AND CELL MANIPULATION
#######################################################

def insert_in_row(worksheet: Worksheet, booking: Booking | None) -> None:
    """
    Insert booking data into worksheet rows.
    
    Parameters:
        worksheet: The worksheet to update
        booking: The booking to insert or None for an empty row
    """
    row = worksheet.row
    if booking:
        for boolean in (False, True):
            worksheet.column.reset()
            
            if boolean and not worksheet.currentBorderRow:
                check_for_border(worksheet)                
            
            for cell in cells():
                cell(worksheet, booking, isDeparture=boolean)
                worksheet.column.increase()
    
            if boolean and not worksheet.latestBorderRow:
                if booking.departure.date > dates.date():
                    worksheet.latestBorderRow = row.number 

            row.increase()  
        row.decrease()
    else:
        insert_empty_row(worksheet)
    worksheet.column.reset()


def insert_empty_row(worksheet: Worksheet) -> None:
    """
    Insert an empty row in the worksheet with default cell formatting.
    
    Parameters:
        worksheet: The worksheet to update
    """
    worksheet.column.reset()
    for cell in cells():
        cell(worksheet)
        worksheet.column.increase()


def skip_departure_rows(worksheet: Worksheet) -> None:
    """
    Skip rows that represent departures and set running totals.
    
    Parameters:
        worksheet: The worksheet to process
    """
    if determine_departure_row(worksheet):     
        check_for_border(worksheet)
        worksheet.column.number = 16
        set_run_tot_cell(worksheet)
        worksheet.row.increase()
    worksheet.column.reset()


def determine_departure_row(worksheet: Worksheet) -> bool:
    """
    Determine if the current row is a departure row based on cell color.
    
    Parameters:
        worksheet: The worksheet to check
        
    Returns:
        True if the current row is a departure row, False otherwise
    """
    column = worksheet.column
    column.number = 2
    cell = worksheet.cell
    if cell.font.color is None:
        return False
    return not cell.isEmpty and cell.font.color.rgb in ('FFFF0000', '00FF0000')


def set_latest_date_border(worksheet: Worksheet) -> None:
    """
    Set borders for the latest date row to highlight current bookings.
    
    Parameters:
        worksheet: The worksheet to update
    """
    current = worksheet.currentBorderRow
    latest = worksheet.latestBorderRow
    if not latest:
        return
    if current == latest:
        return
   
    row = worksheet.row
    column = worksheet.column
    styles = Stylesheet()
    for i, rowNum in enumerate((current, latest)):
        if rowNum is None:
            continue
     
        row.number = rowNum
        cell = worksheet.cell
        styles.borderBottom = 'thick' if i else None

        for colNum in range(1, 18):
            column.number = colNum
            cell.border = styles.border


def check_for_border(worksheet: Worksheet) -> bool:
    """
    Check if the current row has a border and mark it accordingly.
    
    Parameters:
        worksheet: The worksheet to check
        
    Returns:
        True if a border was found, False otherwise
    """
    if worksheet.currentBorderRow:
        return False
        
    if worksheet.cell.hasBorder:
        worksheet.currentBorderRow = worksheet.row.number
        return True
    
    return False


def cells() -> tuple:
    """
    Get the list of cell-setting functions to apply to each row.
    
    Returns:
        Tuple of functions that set cell values in a worksheet row
    """
    return (
        set_id_cell,
        set_date_cell,
        set_time_cell,
        set_details_cell,
        set_lead_guest_cell,
        set_group_cell,
        set_contact_cell,
        set_extras_cell,
        set_meet_greet_cell,
        set_clean_cell,
        set_basic_cell,
        set_additional_cell,
        set_cost_cell,
        set_run_tot_cell,
        set_observations_cell,
    )


def create_new_sheet_for_property(workbook: Workbook, worksheet: Worksheet, property: Property, lastRowNumber: int):
    """
    Create a new worksheet for a property when the current one exceeds row limits.

    Parameters:
        workbook: The workbook containing the worksheets
        worksheet: The existing worksheet to archive
        property: The property for which the new sheet is created
    """
    listsOfData, firstRowTaken = get_last_15_rows_of_data(worksheet, lastRowNumber)

    firstDateTaken = listsOfData[0][1]

    newWorksheet = set_worksheet(name = worksheet.name)
    worksheet.name = f'{worksheet.name} - OLD ({firstDateTaken})'
    workbook.insertSheet(newWorksheet)
    create_worksheet(newWorksheet, property)
    workbook.save()
    
    lastDateTaken = insert_lists_of_data(newWorksheet, listsOfData)

    newOrder = list()
    for name in workbook.sheetnames:
        if name == worksheet.name:
            newOrder.append(newWorksheet.name)
        else:
            newOrder.append(name)
    newOrder.append(worksheet.name)
    workbook.orderSheets(newOrder)
    workbook.save()

    send_email_for_new_sheet(newWorksheet, firstRowTaken)

    return firstDateTaken, lastDateTaken


def get_last_15_rows_of_data(worksheet: Worksheet, lastRowNumber: int) -> tuple[list[int], int]:
    """
    Get the last 15 row numbers of the worksheet.
    
    Parameters:
        worksheet: The worksheet to process
        
    Returns:
        List of the last 15 row numbers
    """
    fifteenRowsOfData = []
    worksheet.row.number = lastRowNumber + 1
    lastDepartureIsBeforeToday = False
    while True:
        worksheet.row.decrease()

        if not fifteenRowsOfData and cells_are_empty(worksheet, (1, 17)):
            continue

        if (
            len(fifteenRowsOfData) > 14 and 
            lastDepartureIsBeforeToday and
            cells_are_empty(worksheet, (1,)) 
        ):
            firstRowTaken = worksheet.row.number
            break

        rowOfData, lastDepartureIsBeforeToday = _get_row_of_data(worksheet, lastDepartureIsBeforeToday)
        fifteenRowsOfData.append(rowOfData)
        
    fifteenRowsOfData.reverse()
    return fifteenRowsOfData, firstRowTaken


def _get_row_of_data(worksheet: Worksheet, lastDepartureIsBeforeToday: bool) -> tuple[list, bool]:
    rowOfData = []
    isDepartureRow = determine_departure_row(worksheet)

    if isDepartureRow and not lastDepartureIsBeforeToday:
        lastDepartureIsBeforeToday = dates.date() > _datetime_or_date_to_date(worksheet.cell.value)
    
    worksheet.column.number = 1
    for i in range(17):
        if i not in (9, 10):
            value = _datetime_or_date_to_date(worksheet.cell.value)
            if isinstance(value, str) and '+' in value and '=' in value:
                value = None
            rowOfData.append(value)
        worksheet.column.increase()
    return rowOfData, lastDepartureIsBeforeToday


def insert_lists_of_data(worksheet: Worksheet, listsOfData: list[list]) -> None:
    worksheet.row.number = 9
    dataCells = cells()

    lastDateTaken = None

    for listOfData in listsOfData:
        worksheet.row.setHeight()
        insert_empty_row(worksheet)
        worksheet.row.increase()
        worksheet.column.reset()
      
        for i in range(len(listOfData)):
            dataCells[i](worksheet=worksheet, value=listOfData[i])
            worksheet.column.increase()
      
        if listOfData[0]:
            lastDateTaken = listOfData[1]
    
    for i in range(15):
        insert_empty_row(worksheet)
        worksheet.row.setHeight()
        worksheet.row.increase()

    return lastDateTaken


def send_email_for_new_sheet(worksheet: Worksheet, lastRowTaken: int) -> None:
    from default.google.mail.functions import new_email, send_email
    user, message = new_email(
        subject=f'New Property Sheet Created for: {worksheet.name}', 
        to='kevin@algarvebeachapartments.com',
        name='Kevin')

    body = message.body
    body.paragraph(
        f'A new property sheet has been created: {worksheet.name}')
    body.paragraph(
        f'The previous sheet was archived and first row used from that sheet was: {lastRowTaken}')
    body.paragraph(
        'You will need to manually copy and paste (Special: Values/Number only)'
        f' the running total (column 16) from that row ({lastRowTaken}) into the new sheet'
        ' at row 9.')
    
    send_email(user=user, message=message, checkSent=True)

#######################################################
# DATA RETRIEVAL FUNCTIONS
#######################################################

def get_property_sheet_properties() -> list[Property]:
    """
    Get properties with owner information for property sheets.
    
    Returns:
        List of properties with owner details loaded
    """
    search = search_properties()
    select = search.propertyOwners.select()
    select.id()
    select.name()
    select.email()
    select.phone()
    select.nifNumber()
    return search


def get_property_sheet_bookings(
    database: Database | None = None, 
    start: date | None = None, 
    end: date | None = None, 
    propertyName: str | None = None
) -> Database:
    """
    Get bookings for property sheets with all required details.
    
    Parameters:
        database: Optional database connection
        start: Optional start date for filtering bookings
        end: Optional end date for filtering bookings
        propertyName: Optional property name to filter bookings
        
    Returns:
        List of bookings with all required details loaded
    """
    search = search_bookings(database, start=start, end=end, propertyName=propertyName)
    
    # Select details from bookings table
    select = search.details.select()
    select.isOwner()
    select.adults()
    select.children()
    select.babies()
    select.enquiryStatus()
    select.enquirySource()

    search.arrivals.select().all()
    search.extras.select().all()
    search.departures.select().all()

    select = search.properties.select()
    select.name()
    select.shortName()
    select.standardCleaningFee()
    select.weClean()
    select.weBook()

    select = search.propertyOwners.select()
    select.isPaidRegularly()
    
    # Select from property specs
    select = search.propertySpecs.select()
    select.bedrooms()
    
    # Select from guest
    select = search.guests.select()
    select.firstName()
    select.lastName()
    select.phone()
    select.email()
    
    return search


def get_property_sheet_booking(
    database: Database | None = None, 
    bookingId: str | None = None
) -> Booking:
    """
    Get a single booking for property sheets with all details.
    
    Parameters:
        database: Optional database connection
        bookingId: ID of the booking to retrieve
        
    Returns:
        Single booking with all required details loaded
    """
    search = get_property_sheet_bookings(database)
    
    select = search.emails.select()
    select.arrivalQuestionnaire()
    select.management()

    select = search.properties.select()
    select.sendOwnerBookingForms()
    
    where = search.details.where()
    where.id().isEqualTo(bookingId)
    return search.fetchone()


def sort_owner_properties(properties: list[Property]) -> dict[str, list[Property]]:
    """
    Sort properties by owner name.
    
    Parameters:
        properties: List of properties to sort
        
    Returns:
        Dictionary mapping owner names to their properties
    """
    if not properties:
        return {}
 
    result = {}
    for property in properties:
        owner = property.owner.name
 
        if owner not in result:
            result[owner] = []
 
        result[owner].append(property)
    return result


def _datetime_or_date_to_date(value: datetime | date) -> date:
    if isinstance(value, datetime):
        return value.date()
    return value