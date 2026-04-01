from default.booking.booking import Booking
from interface.functions import get_text, get_int
from interfaces.interface import Interface


def update_details(
    subsection: Interface, 
    databaseBooking: Booking, 
) -> None:
    """
    Update the booking status in the database.
    
    Parameters:
        subsection: Interface object for user interaction
        databaseBooking: Current booking object from the database
    """
    options = [
        'Set PIMS Id',
        'Set Enquiry Source',
        'Set Platform Id',
        'Set Property',
        'Set "Booking confirmed"',
        'Set "Booking cancelled"',
        'Set "Booking cancelled with fees"',
        'Set "Booking confirmed as replacement"',
    ]

    subsection.section(
        f'Change booking details? (Current status: {databaseBooking.details.enquiryStatus})'
    )
    option = subsection.option(options)

    if option is None:
        return None
    
    if option == 1:
        pims_id = get_int(subsection, 'PIMS Id', databaseBooking.details.PIMSId)
        if pims_id is None:
            return None
        databaseBooking.details.PIMSId = pims_id
    elif option == 2:
        enquiry_source = get_text(subsection, 'Enquiry Source', databaseBooking.details.enquirySource)
        if enquiry_source is None:
            return None
        databaseBooking.details.enquirySource = enquiry_source
    elif option == 3:
        platform_id = get_text(subsection, 'Platform Id', databaseBooking.details.platformId)
        if platform_id is None:
            return None
        databaseBooking.details.platformId = platform_id
    elif option == 4:
        property_name = get_text(subsection, 'Property', databaseBooking.property.name)
        if property_name is None:
            return None
        databaseBooking.details.propertyId = property_name.upper()
    elif option < 9:
        newStatus = options[option - 1].split('Set "')[1][:-1]
        if databaseBooking.details.enquiryStatus == newStatus:
            return None
        subsection.text(f'Changing booking status to "{newStatus}"?')
        databaseBooking.details.enquiryStatus = newStatus
    
    databaseBooking.update()