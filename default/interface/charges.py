from default.booking.booking import Booking
from default.interface.functions import get_float, get_bool
from libraries.interface.interface import Interface


def update_charges(subsection: Interface, databaseBooking: Booking) -> None:
    """
    Update financial charges for a booking.
    
    Presents a menu of charge types that can be modified and processes
    the user's selection. Updates the booking with any changes made.
    Supports changing extra nights charges, basic rental charges, and 
    platform fees.
    
    Parameters:
        subsection: Interface object for user interaction
        databaseBooking: Original booking data from the database
    
    Returns:
        None if user exits, otherwise recursively continues updating
    """
    subsection.section('Updating charges for selected booking. Which are we changing?')
    
    charges = [
        'Extra Nights Charge',
        'Basic Rental Charge',
        'Platform Fee',
        'Admin Fee',
        'Tourist Tax Total',
        'Tourist Tax Paid',
    ]
    
    charge = subsection.option(charges)

    if charge is None:
        return None

    manual = databaseBooking.charges.manualCharges

    if charge == 1:
        current = databaseBooking.charges.extraNights
        
        value, manual = get_float(subsection, charges[charge - 1], current, manual)
        
        databaseBooking.charges.extraNights = value
        databaseBooking.charges.manualCharges = manual

    elif charge == 2:
        currentBasic = databaseBooking.charges.basicRental
        
        value, manual = get_float(subsection, charges[charge - 1], currentBasic, manual)
        
        databaseBooking.charges.basicRental = value
        databaseBooking.charges.manualCharges = manual
    
    elif charge == 3:
        currentPlatformFee = databaseBooking.charges.platformFee
        
        value, manual = get_float(subsection, charges[charge - 1], currentPlatformFee, manual)
        
        databaseBooking.charges.platformFee = value
        databaseBooking.charges.manualCharges = manual

    elif charge == 4:
        currentAdminFee = databaseBooking.charges.adminFee
        
        value, manual = get_float(subsection, charges[charge - 1], currentAdminFee, manual)
        
        databaseBooking.charges.adminFee = value
        databaseBooking.charges.manualCharges = manual

    elif charge == 5:
        currentTouristTaxTotal = databaseBooking.charges.touristtax.total
        
        value, manual = get_float(subsection, charges[charge - 1], currentTouristTaxTotal, manual)
        
        databaseBooking.charges.touristtax.total = value

    elif charge == 6:
        currentTouristTaxPaid = databaseBooking.charges.touristtax.paid
        
        value = get_bool(subsection, 'Tourist Tax Paid', currentTouristTaxPaid)
        
        databaseBooking.charges.touristtax.paid = value

    databaseBooking.update()
    
    return update_charges(subsection, databaseBooking)