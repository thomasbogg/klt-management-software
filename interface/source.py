from datetime import date
from default.booking.booking import Booking
from default.dates import dates
from PIMS.download import download_latest_from_PIMS
from platforms.airbnb.download import update_from_airbnb
from platforms.bookingCom.download import update_from_bookingCom
from platforms.vrbo.download import update_from_vrbo
from sheets.KKLJ.run import update_KKLJ_properties_sheets


def update_at_source(booking: Booking) -> None:
    """
    Update booking information from its original source platform.
    
    Fetches the latest booking data from the source platform (PIMS, Airbnb, 
    Booking.com, or Vrbo) based on the booking's enquiry source. For direct
    bookings, downloads from PIMS. For platform bookings, calls the appropriate
    platform update function.
    
    Parameters:
        booking: Booking object to update from source
    
    Returns:
        None, though some platform update functions may return values
    """
    source = booking.details.enquirySource

    if source == 'Direct':
        return download_latest_from_PIMS(visible=True, PIMSId=booking.details.PIMSId)
        
    if source == 'Airbnb':
        return update_from_airbnb(id=booking.details.platformId)

    if source == 'KKLJ':
        return update_KKLJ_properties_sheets(
                                            start=booking.arrival.date, 
                                            propertyName=booking.property.shortName)
        
    arrivalDate = booking.arrival.date
    if source == 'Vrbo':
        return update_from_vrbo(start=arrivalDate, end=dates.calculate(arrivalDate, days=1))

    location = booking.property.address.location
    update_from_bookingCom(start=arrivalDate, end=arrivalDate, properties=(location,))

    return None