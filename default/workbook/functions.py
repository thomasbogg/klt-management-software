from datetime import date
from os import path

from default.booking.booking import Booking
from default.booking.functions import (
    determine_hide_charges,
    determine_use_exchange_rate,
    logbooking
)
from default.dates import dates
from default.settings import LOCAL_STORAGE_DIR
from workbooks.dates import WorksheetDates
from workbooks.workbook import Workbook
from workbooks.worksheet import Worksheet


#######################################################
# WORKBOOK AND WORKSHEET CREATION FUNCTIONS
#######################################################

def get_workbook(filename: str, subfolder: str = '') -> Workbook:
    """
    Create or open a workbook with the specified filename in the given subfolder.
    
    Args:
        filename: The name of the workbook file.
        subfolder: Optional subfolder within LOCAL_STORAGE_DIR.
        
    Returns:
        The initialized Workbook object.
    """
    directory = path.join(LOCAL_STORAGE_DIR, subfolder)
    return Workbook(filename, directory)


def set_worksheet(name: str, start: date | int = None, end: date | int = None, 
                 checkExchange: bool = False, checkHide: bool = False, 
                 stringDates: bool = False, internal: bool = False) -> Worksheet:
    """
    Create and configure a worksheet with the specified settings.
    
    Args:
        name: The name of the worksheet.
        start: Optional start date or row number for filtering data.
        end: Optional end date or row number for filtering data.
        checkExchange: Whether to check exchange rates for bookings.
        checkHide: Whether to check if charges should be hidden.
        stringDates: Whether dates should be handled as strings.
        
    Returns:
        The configured Worksheet object.
    """
    worksheet = Worksheet(name)
    worksheet.start = start
    worksheet.end = end
    worksheet.checkExchange = checkExchange
    worksheet.checkHide = checkHide
    worksheet.stringDates = stringDates
    worksheet.internal = internal

    row = worksheet.row
    row.firstDataRow = 2
    row.maxEmptiesAllowed = 1
    row.defaultHeight = 30
    
    column = worksheet.column
    column.firstDataColumn = 1
    return worksheet


def create_worksheet(worksheet: Worksheet, bookings: list[Booking] | None, 
                    cells: tuple) -> Worksheet:
    """
    Create a new worksheet with headers and booking data.
    
    Args:
        worksheet: The worksheet to populate.
        bookings: List of booking objects to add to the worksheet.
        cells: Tuple of cell setter functions to apply to each booking.
        
    Returns:
        The populated Worksheet object.
    """
    row = worksheet.row
    row.number = row.headerRow
    row.height = 35
    row.freeze()

    column = worksheet.column
    column.number = column.firstDataColumn

    for booking in [None] + (bookings or []):
        if booking:
            if booking.details.statusIsNotOkay:
                continue
            logbooking(booking, inline='NEW booking:')

        for col in cells:
            worksheet = col(worksheet, booking)
            worksheet.column.increase()

        worksheet.row.increase()
        worksheet.row.height = 30
        worksheet.column.number = column.firstDataColumn

    return worksheet


def update_worksheet(worksheet: Worksheet, bookings: list[Booking], 
                    cells: tuple, startEndCol: int) -> Worksheet:
    """
    Update an existing worksheet with booking data.
    
    Args:
        worksheet: The worksheet to update.
        bookings: List of booking objects to add or update in the worksheet.
        cells: Tuple of cell setter functions to apply to each booking.
        startEndCol: Column index used to determine start/end dates.
        
    Returns:
        The updated Worksheet object.
    """
    worksheet.row.number = worksheet.row.firstDataRow - 1
    return _update_worksheet(worksheet, bookings, cells, startEndCol)


#######################################################
# DATA INSERTION AND ROW MANIPULATION FUNCTIONS
#######################################################

def insert_bookings(worksheet: Worksheet, bookings: list[Booking], 
                   cells: tuple) -> Worksheet:
    """
    Insert multiple bookings into a worksheet sequentially.
    
    Args:
        worksheet: The worksheet to insert bookings into.
        bookings: List of booking objects to insert.
        cells: Tuple of cell setter functions to apply to each booking.
        
    Returns:
        The modified Worksheet object.
    """
    row = worksheet.row
    row.number = row.firstDataRow
    for booking in bookings:
        row.height = 30
        worksheet = insert_in_row(worksheet, booking, cells)
        row.increase()
    return worksheet


def insert_in_row(worksheet: Worksheet, booking: Booking | None, cells: tuple) -> Worksheet:
    """
    Insert booking data into the current worksheet row.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking object to insert, or None for an empty row.
        cells: Tuple of cell setter functions to apply.
        
    Returns:
        The modified Worksheet object.
    """
    worksheet.column.number = worksheet.column.firstDataColumn
    if booking and worksheet.checkExchange:
        booking.charges.applyExchangeRate = determine_use_exchange_rate(booking)
    if booking and worksheet.checkHide:
        booking.charges.hide = determine_hide_charges(booking)
    for cell in cells:
        worksheet = cell(worksheet, booking)
        worksheet.column.increase()
    return worksheet


def insert_empty_row(worksheet: Worksheet, cells: tuple) -> Worksheet:
    """
    Insert an empty row with specified cell formatting.
    
    Args:
        worksheet: The worksheet to modify.
        cells: Tuple of cell setter functions to apply.
        
    Returns:
        The modified Worksheet object.
    """
    for cell in cells:
        worksheet = cell(worksheet)
        worksheet.column.increase()
    return worksheet


#######################################################
# DATE AND ROW CHECKING FUNCTIONS
#######################################################

def cells_are_empty(worksheet: Worksheet, colNums: tuple[int, ...]) -> bool:
    """
    Check if specified columns in the current row are empty.
    
    Args:
        worksheet: The worksheet to check.
        colNums: Tuple of column numbers to check.
        
    Returns:
        True if all specified cells are empty, False otherwise.
    """
    for colNum in colNums:
        worksheet.column.number = colNum
        if not worksheet.cell.isEmpty:
            worksheet.column.reset()
            return False
    worksheet.column.reset()    
    return True


def row_date_is_before_start_date(worksheet: Worksheet, startEndCol: int | None) -> bool | None:
    """
    Check if the date in the current row is before the worksheet start date.
    
    Args:
        worksheet: The worksheet to check.
        startEndCol: The column number containing the date to check.
        
    Returns:
        True if the row date is before start date, False if not, None if no date found.
    """
    if not hasattr(worksheet, 'start') or worksheet.start is None:
        return False
 
    worksheet.column.number = startEndCol
    value = worksheet.cell.value

    if value is None:
        return None
    
    if hasattr(worksheet, 'stringDates') and worksheet.stringDates:
        value = WorksheetDates.toDatetimeDate(value)
    
    if dates.isDatetimeDatetime(value):
        value = value.date()
   
    result = value < worksheet.start
    return result


def row_date_is_after_end_date(worksheet: Worksheet, startEndCol: int | None) -> bool | None:
    """
    Check if the date in the current row is after the worksheet end date.
    
    Args:
        worksheet: The worksheet to check.
        startEndCol: The column number containing the date to check.
        
    Returns:
        True if the row date is after end date, False if not, None if no date found.
    """
    if not hasattr(worksheet, 'end') or worksheet.end is None:
        return False
 
    worksheet.column.number = startEndCol    
    value = worksheet.cell.value

    if value is None:
        return None
    
    if hasattr(worksheet, 'stringDates') and worksheet.stringDates:
        value = WorksheetDates.toDatetimeDate(value)
    
    if dates.isDatetimeDatetime(value):
        value = value.date()
  
    result = value > worksheet.end
    return result


def id_not_in_bookings(bookings: list[Booking], rowId: int) -> bool:
    """
    Check if the specified ID is not in the list of bookings.
    
    Args:
        bookings: List of booking objects to check against.
        rowId: The ID to look for.
        
    Returns:
        True if the ID is not found in any booking, False otherwise.
    """
    return not any(booking.id == rowId for booking in bookings)


#######################################################
# ORDERING AND SORTING FUNCTIONS
#######################################################

def determine_months_order(sheetnames: list[str]) -> list[str]:
    """
    Determine the optimal order of months based on current date.
    
    Args:
        sheetnames: List of sheet names that may include month names.
        
    Returns:
        A list of month names in the optimal order.
    """
    months = dates.stringMonths()
    monthIndex = dates.month() - 1
    month = months[monthIndex]
    day = dates.day()
    order = [month]
  
    if day > 15 and monthIndex != 11: 
        order += [months[monthIndex + 1]]
    elif monthIndex != 0: 
        order += [months[monthIndex - 1]]
  
    order += [m for m in months if m not in order and m in sheetnames]
    return order


def determine_years_order(sheetnames: list) -> list:
    """
    Determine the optimal order of years based on current date.
    
    Args:
        sheetnames: List of sheet names that may include year numbers.
        
    Returns:
        A list of years in the optimal order.
    """
    year = dates.year()
    order = [year]
    if dates.month() == 1 and 15 < dates.day() < 19: 
        order += [year - 1]
    order += [y for y in sorted(sheetnames) if int(y) not in order]
    return [str(y) for y in order]


#######################################################
# PRIVATE FUNCTIONS
#######################################################

def _update_worksheet(
        worksheet: Worksheet, 
        bookings: list[Booking], 
        cells: tuple, 
        startEndCol: int | None = None) -> Worksheet:
    """
    Recursively update a worksheet by processing rows and inserting bookings.
    
    Args:
        worksheet: The worksheet object to be updated.
        bookings: A list of booking objects to be inserted into the worksheet.
        cells: A tuple of cell setter functions to apply to each booking.
        startEndCol: The column index used to determine start and end dates.
        
    Returns:
        The updated worksheet object.
    
    This function processes rows recursively, checking conditions such as empty cells,
    row dates, and booking IDs to determine whether to insert, delete, or skip rows.
    Bookings are inserted sequentially from the provided list, and the list is modified
    in-place as bookings are processed.
    """
    row = worksheet.row
    if row.atMaxEmpties:
        return worksheet

    row.increase()
    row.setHeight()

    if cells_are_empty(worksheet, (1,)):
        row.increaseEmptyCount()
       
        if bookings:
            row.resetEmptyCount()
            booking = bookings.pop(0)
            logbooking(booking, inline='NEW booking:')
        else:
            booking = None
    
        insert_in_row(worksheet, booking, cells)
        return _update_worksheet(worksheet, bookings, cells, startEndCol)

    row.resetEmptyCount()

    if row_date_is_before_start_date(worksheet, startEndCol):
        return _update_worksheet(worksheet, bookings, cells, startEndCol)

    if row_date_is_after_end_date(worksheet, startEndCol):
        if bookings:
            row.insert()
            booking = bookings.pop(0)
            logbooking(booking, inline='NEW booking:')
        else:
            booking = None
  
        insert_in_row(worksheet, booking, cells)
        return _update_worksheet(worksheet, bookings, cells, startEndCol)
    
    if bookings:
        booking = bookings[0]
        worksheet.column.reset()
        rowId = worksheet.cell.value
    
        if booking.id != rowId:
            if id_not_in_bookings(bookings, rowId):
                row.delete()
                row.decrease()
                return _update_worksheet(worksheet, bookings, cells, startEndCol)
    
            row.insert()
            logbooking(booking, inline='NEW booking:')
    
        booking = bookings.pop(0)
        insert_in_row(worksheet, booking, cells)
        return _update_worksheet(worksheet, bookings, cells, startEndCol)
    
    row.delete()
    row.decrease()
    return _update_worksheet(worksheet, bookings, cells, startEndCol)