"""
Tourist Tax Management Module

This module provides functionality for managing property registrations
in the Albufeira tourist tax system (TMT). It handles adding new properties
to the system and querying existing property data from the database.
"""

from datetime import datetime
from typing import Optional

from default.database.functions import get_database
from default.update.dates import updatedates
from default.update.wrapper import update
from touristtax.browser import TMTBrowser
from touristtax.functions import get_tourist_tax_properties, get_tourist_tax_bookings, calculate_tourist_tax
from libraries.utils import log, sublog


@update
def add_new_tourist_tax_properties(propertyId: Optional[int] = None, propertyName: Optional[str] = None) -> None:
    """
    Add new properties to the TMT (Tourist Tax Management) system.
    
    This function retrieves properties from the database based on the provided
    criteria and registers them in the Albufeira tourist tax system through
    automated browser interactions.
    
    Args:
        propertyId (Optional[int]): Specific property ID to add (default: None)
        propertyName (Optional[str]): Property name pattern to search for (default: None)
        
    Note:
        - If both parameters are None, all eligible properties will be processed
        - Only properties with weBook=True and valid AL numbers are processed
        - Existing properties are automatically skipped
        - Browser runs in visible mode for monitoring progress
    """
    # Get properties matching the specified criteria
    properties = get_tourist_tax_properties(propertyId, propertyName)
    
    # Initialize browser in visible mode for monitoring
    browser = TMTBrowser(visible=False)
    browser.goTo()
    browser.login()

    # Process each property for TMT registration
    for property in properties:
        log(f'Adding property {property.name} to TMT')
        
        # Navigate to properties list to check existence
        browser.goToPropertiesList()
        
        # Skip if property already exists in TMT
        if browser.propertyExists(property):
            sublog(f'Property {property.name} already exists in TMT, skipping')
            continue
            
        # Add new property to TMT system
        browser.addNewProperty(property)
        
        # Return to properties list for next iteration
        browser.goToPropertiesList()

    browser.quit()  # Close browser after processing all properties
    return 'Successfully added properties to TMT'


def pay_monthly_tourist_tax(start: datetime.date = None, end: datetime.date = None, propertyName: str | None = None) -> None:
    """
    Pay the monthly tourist tax for a specific property.
    
    This function calculates the tourist tax based on the property's bookings
    and specifications, then automates the payment process through the TMT
    system.
    
    Args:
        propertyId (int): The ID of the property for which to pay the tax
        start (datetime.date): The start date for the booking search
        end (datetime.date): The end date for the booking search

    Note:
        - The function retrieves all valid bookings for the property within the specified date range
        - The tax is calculated based on the number of guests and the property's specifications
        - The payment process is automated through browser interactions with the TMT system
    """
    if start is None or end is None:
        start, end = updatedates.tourist_tax_payment_dates()

    properties = get_tourist_tax_properties(propertyName=propertyName)
    database = get_database()

    browser = TMTBrowser(visible=True)
    browser.goTo()
    browser.login()
    
    for property in properties:
        log(f'Processing tourist tax payment for property {property.name}')
       
        browser.goToMonthlyDeclarations()
        if not browser.propertyExists(property):
            sublog(f'Property {property.name} does not exist in TMT, skipping tax payment')
            continue
        
        # Get bookings for the property within the specified date range
        bookings = get_tourist_tax_bookings(database, start, end, property.name)
        
        # Calculate the total tourist tax based on bookings and property specifications
        tax_amount = calculate_tourist_tax(bookings)

        sublog(f'Calculated tourist tax for property {property.name}: {tax_amount:.2f}')
        browser.declareMonthlyTax(property=property, year=start.year, month=start.month, total=tax_amount)
        browser.home()  # Return to home after declaration

    browser.quit()  # Close browser after processing all properties
    return 'Successfully paid monthly tourist tax for properties'