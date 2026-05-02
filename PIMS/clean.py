from datetime import date
from PIMS.browser import BrowsePIMS
from default.update.wrapper import update
from utils import sublog


@update
def delete_cancelled_platform_bookings_in_PIMS(start: date = None, end: date = None, visible: bool = False) -> str:
    """
    Delete cancelled platform bookings from PIMS.
    
    Finds and removes cancelled bookings that were imported via iCal within the 
    specified date range. This helps keep the PIMS system clean by removing stale
    cancelled bookings from third-party platforms.
    
    Parameters:
        start: Start date for filtering bookings
        end: End date for filtering bookings
        visible: Whether to show the browser window during execution
    
    Returns:
        Success message confirming deletion
    """
    browser = BrowsePIMS(visible).goTo().login()
    reservations = get_reservations(browser.reservations.goTo(), start, end)
    
    for reservation in reservations:
        pimsId = reservation['orderId']
        guest = reservation['guest']
        arrival = reservation['arrival']
        status = reservation['status']
        sublog(f'Deleting {status} {pimsId} for {guest} of date {arrival}')
        browser.orderForms.goTo(pimsId).deleteBooking()
    
    browser.quit()
    return 'All cancelled iCal import bookings deleted successfully'
    

def get_reservations(browser: BrowsePIMS.ReservationsList, start: date, end: date) -> list[dict]:
    """
    Get a list of cancelled iCal bookings from PIMS.
    
    Configures the search parameters on the reservations list page
    to find only cancelled bookings imported via iCal within the
    specified date range.
    
    Parameters:
        browser: PIMS reservations list interface
        start: Start date for filtering bookings
        end: End date for filtering bookings
    
    Returns:
        List of dictionaries containing booking information
    """
    browser.propertyName = 'All Properties'
    browser.start = start
    browser.end = end
    browser.resultsType = 'All Cancelled bookings'
    browser.sortBy = 'start_date'
    browser.iCalOnly = True
    browser.onlyOwner = False
    browser.noOwner = False
    browser.update()
    return browser.list