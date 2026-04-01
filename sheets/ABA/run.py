from datetime import date, datetime
import re

from dates import dates
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import (
    get_database, 
    search_valid_bookings, 
    set_valid_accounts_booking
)
from default.google.drive.functions import (
    download_drive_file_to_local_storage, 
    upload_local_file_to_drive
)
from default.property.property import Property
from default.update.dates import updatedates
from default.update.wrapper import update
from sheets.functions import (
    args_for_drive,
    create_worksheet,
    get_property_sheet_bookings, 
    get_property_sheet_properties, 
    get_workbook,
    set_worksheet,
    sort_owner_properties,
    update_worksheet
)
from utils import log, sublog, toList
from workbooks.workbook import Workbook


#######################################################
# MAIN UPDATE FUNCTION
#######################################################

@update
def update_ABA_properties_sheets(
    start: date | None = None, 
    end: date | None = None, 
    propertyNames: list[str] | str | None = None,
    updateAll: bool = False,
) -> str:
    """
    Update property sheets for Algarve Beach Apartments (ABA) properties.
    
    Downloads or creates property sheets, updates them with booking information,
    and uploads them back to Google Drive.
    
    Parameters:
        start: Start date for bookings to include
        end: End date for bookings to include
        propertyNames: Specific property names to update, or None for all ABA properties
        updateAll: If True, update all properties regardless of arrival dates
        
    Returns:
        Success message string
    """
    if start is None and end is None: 
        start, end = updatedates.ABA_sheets_update_dates()

    propertyNames = toList(propertyNames)
    database = get_database()
    ownersProperties = get_ABA_properties(database, propertyNames, updateAll=updateAll)
    newFile = False

    newSheets: list[dict[str, tuple[date, date]]] = list()

    for owner, properties in ownersProperties.items():
        if propertyNames and not any(property.shortName in propertyNames for property in properties): 
            continue
        
        log(f'UPDATING: {", ".join([property.shortName for property in properties])}...')
        
        file = download_drive_file_to_local_storage(**args_for_drive(owner), match=False)
        if file:
            workbook = get_workbook(f'{file.name}').load()
        else:
            sublog('file does not exist in Google Drive. Creating new file...')
            filename = f'{", ".join([property.shortName for property in properties])} - {owner}.xlsx'
            workbook = get_workbook(f'{filename}').create()
            newFile = True

        for property in properties: 
            newSheetDates = update_property_sheet(database, workbook, property, start, end, newFile)
            if newSheetDates:
                sublog(f'CREATED new sheet for property: {property.shortName}. Will need to reupdate after.')
                newSheets.append({property.shortName: newSheetDates})
        
        workbook.save()
        upload_local_file_to_drive(file, **args_for_drive(f'{workbook.name}'))

    for newSheet in newSheets:
        for propertyName, sheetDates in newSheet.items():
            log(f'Reupdating new sheet for property: {propertyName}...')
            update_ABA_properties_sheets(start=sheetDates[0], end=sheetDates[1], propertyNames=[propertyName])

    database.close()
    return 'Successfully updated all ABA Properties Sheets!'


#######################################################
# HELPER FUNCTIONS
#######################################################

def update_property_sheet(
    database: Database, 
    workbook: Workbook, 
    property: Property, 
    start: date | None, 
    end: date | None,
    newFile: bool,
) -> tuple[date, date] | None:
    """
    Update a single property worksheet within a workbook.
    
    Parameters:
        database: Database connection
        workbook: Excel workbook to update
        property: Property object containing property information
        start: Start date for bookings to include
        end: End date for bookings to include
    """
    sheetName = property.shortName

    for _sheetname in workbook.sheetnames:
        if not _sheetname.startswith(sheetName):
            continue

        oldSheet = re.search(r'OLD \((.+)\)', _sheetname)
        if oldSheet:
            strDate = oldSheet.group(1)
            year, month, day = strDate.split('-')
            oldDate = dates.date(year, month, day)

            if oldDate and oldDate > end:
                return None
            
            if oldDate and oldDate > start:
                start = oldDate

    bookings = get_ABA_bookings(database, start, end, sheetName)

    if not bookings and not newFile:
        return None
    
    sublog(f'doing sheet: {sheetName}...')
    sheet = set_worksheet(name=sheetName, start=start, end=end)
    
    if not workbook.hasSheet(sheet):
        workbook.insertSheet(sheet)
        create_worksheet(sheet, property)
        skipFirstRow = False
    else:
        workbook.openSheet(sheet)
        skipFirstRow = True
    
    return update_worksheet(workbook, sheet, bookings, property, skipFirstRow=skipFirstRow)


def get_ABA_properties(
    database: Database, 
    propertyNames: list[str] | None = None,
    updateAll: bool = False,
) -> dict[str, list[Property]]:
    """
    Get properties belonging to Algarve Beach Apartments (ABA).
    
    Returns properties either filtered by provided names or by arrival dates
    if it's not Sunday.
    
    Parameters:
        database: Database connection
        propertyNames: Optional list of property names to filter by
        
    Returns:
        Dictionary mapping owner names to lists of their properties
    """
    propertyIds = None
    isSunday = updatedates.is_Sunday() 
    
    if not propertyNames:
        arrivalDates = updatedates.ABA_sheets_update_arrival_dates()
        search = search_valid_bookings(database)
        where = search.arrivals.where()
        where.date().isIn(arrivalDates)
        bookings = search.fetchall()
        propertyIds = set(booking.details.propertyId for booking in bookings)
    
    search = get_property_sheet_properties()
    where = search.properties.where()
    where.weBook().isTrue()
    
    if propertyNames:
        where.shortName().isIn(propertyNames)
    elif not isSunday and not updateAll:
        where.id().isIn(propertyIds)
    
    return sort_owner_properties(search.fetchall())


def get_ABA_bookings(
    database: Database, 
    start: date | None, 
    end: date | None, 
    propertyName: str
) -> list[Booking]:
    """
    Get ABA bookings filtered by date range and property name.
    
    Parameters:
        database: Database connection
        start: Start date for bookings to include
        end: End date for bookings to include
        propertyName: Name of the property to get bookings for
        
    Returns:
        List of booking objects matching the criteria
    """
    search = get_property_sheet_bookings(database, start, end, propertyName)
    
    select = search.charges.select()
    select.basicRental()
    select.platformFee()
    select.currency()
    
    select = search.propertyOwners.select()
    select.wantsAccounting()
    select.isPaidRegularly()
    select.rentalCommissionsAreInvoiced()
    
    select = search.details.select()
    select.enquirySource()
    select.enquiryStatus()
    
    set_valid_accounts_booking(search)
    
    if propertyName:
        where = search.properties.where()
        where.shortName().isEqualTo(propertyName)
    
    return search.fetchall()