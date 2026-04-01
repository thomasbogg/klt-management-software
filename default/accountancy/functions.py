from datetime import date
from default.database.database import Database
from default.database.functions import search_bookings, set_valid_accounts_booking, get_property
from default.property.accountant import Accountant
from default.settings import LOCAL_STORAGE_DIR
import os


#######################################################
# DIRECTORY SETTINGS
#######################################################

ACC_STORAGE_DIR = os.path.join(LOCAL_STORAGE_DIR, 'accountancy-sheets')


#######################################################
# DATABASE QUERY FUNCTIONS
#######################################################

def get_accountancy_sheet_bookings(
        database: Database, 
        start: date = None, 
        end: date = None, 
        noOwner: bool = True) -> Database:
    """
    Retrieves bookings data for accountancy sheets with specified conditions.

    Args:
        database: The database connection object
        start: The start date for filtering bookings
        end: The end date for filtering bookings
        noOwner: Whether to exclude owner bookings

    Returns:
        A search object with the selected data and applied conditions
    """
    search = search_bookings(database, start, end)
  
    # Select details data
    select = search.details.select()
    select.enquiryStatus()
    select.enquirySource()
    select.isOwner()
  
    # Select arrival data
    select = search.arrivals.select()
    select.date()
    
    # Select departures data
    select = search.departures.select()
    select.date()
  
    # Select property data
    select = search.properties.select()
    select.name()
    select.shortName()
    select.weClean()
    select.standardCleaningFee()
  
    # Select guests data
    select = search.guests.select()
    select.all()
    
    # Select charges data
    select = search.charges.select()
    select.currency()
    select.basicRental()
    select.platformFee()
  
    # Select property owners data
    select = search.propertyOwners.select()
    select.name()
    select.wantsAccounting()
    select.takesEuros()
    select.takesPounds()
    select.rentalCommissionsAreInvoiced()
  
    # Set conditions for bookings
    set_valid_accounts_booking(search)
  
    if noOwner:
        search.details.where().isOwner().isNullEmptyOrFalse()
  
    return search


def get_property_accountant(
    propertyName: str
) -> Accountant:
    """
    Get the accountant name and email for a specific property.
    
    Args:
        database: Database instance
        propertyName: Name of the property
    Returns:
        Accountant object containing the accountant's details
    """
    search = get_property(name=propertyName)
    select = search.propertyAccountants.select()
    select.name()
    select.email()

    property = search.fetchone()
    if not property:
        raise ValueError(f'No accountants found for property: {propertyName}')

    return property.accountant
