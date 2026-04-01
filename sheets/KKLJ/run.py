from datetime import date
from default.database.functions import get_database
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
    get_filename,
    get_property_sheet_properties,
    get_workbook,
    sort_owner_properties
)
from sheets.KKLJ.functions import set_KKLJ_worksheet, update_worksheet
from utils import log, sublog


#######################################################
# MAIN UPDATE FUNCTION
#######################################################

@update
def update_KKLJ_properties_sheets(
    start: date | None = None, 
    propertyName: str | None = None
) -> str:
    """
    Update property sheets for KKLJ properties.
    
    Downloads or creates property sheets, updates them with booking information,
    and uploads them back to Google Drive.
    
    Parameters:
        start: Start date for bookings to include
        propertyName: Specific property name to update, or None for all KKLJ properties
        
    Returns:
        Success message string
    """
    if start is None: 
        start = updatedates.KKLJ_sheets_update_dates()

    database = get_database()
    ownerProperties = sort_owner_properties(get_KKLJ_properties())
    
    for owner, properties in ownerProperties.items():
        filename = get_filename(owner=owner, properties=properties)
        if propertyName and propertyName not in filename: 
            continue
            
        log(f'UPDATING: {filename}...')
        file = download_drive_file_to_local_storage(**args_for_drive(filename))
        
        if file:
            workbook = get_workbook(filename=filename).load()
        else:
            sublog('file does not exist in Google Drive. Creating new file...')
            workbook = get_workbook(filename=filename).create()

        for property in properties:
            sheetName = property.shortName
            if propertyName and sheetName != propertyName:
                continue
            
            sublog(f'Doing sheet: {sheetName}...')
            sheet = set_KKLJ_worksheet(sheetName, property, start)
            
            if workbook.hasSheet(sheet): 
                workbook.openSheet(sheet)
            else:
                workbook.insertSheet(sheet)
                create_worksheet(sheet, property)
                
            update_worksheet(database, sheet)

        workbook.save()
        upload_local_file_to_drive(file, **args_for_drive(filename))

    database.close()
    return 'Successfully updated from all KKLJ Properties Sheets!'


#######################################################
# HELPER FUNCTIONS
#######################################################

def get_KKLJ_properties() -> list[Property]:
    """
    Get properties managed by KKLJ.
    
    Fetches all properties that:
    - Are not booked by us (weBook is False)
    - Are cleaned by us (weClean is True)
    
    Returns:
        List of Property objects matching the criteria
    """
    search = get_property_sheet_properties()
  
    select = search.properties.select()
    select.sendOwnerBookingForms()

    where = search.properties.where()
    where.weBook().isFalse()
    where.weClean().isTrue()
  
    return search.fetchall()