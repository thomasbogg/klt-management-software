from default.booking.booking import Booking
from interface.functions import get_text
from interfaces.interface import Interface


def update_forms(subsection: Interface, booking: Booking) -> None:
    """
    Update form details for a booking.
    
    Presents a menu of form types that can be modified and processes
    the user's selection. Updates the booking with any changes made.
    Supports updating security deposit forms, guest registration forms,
    balance payment forms, arrival questionnaires, and marking guest
    registration as complete.
    
    Parameters:
        subsection: Interface object for user interaction
        booking: Booking object containing form information to update
    
    Returns:
        None if user exits, otherwise recursively continues updating
    """
    subsection.section('Updating Form details for selected booking')
    
    details = [
        'Security Deposit',
        'Guest Registration',
        'Balance Payment',
        'Arrival Questionnaire',
        'Set Guest Registration Form as Done',
    ]
    
    detail = subsection.option(details)

    if detail is None:
        return None

    if detail == 1:
        newForm = get_text(subsection, details[detail - 1], booking.forms.securityDeposit)
        booking.forms.securityDeposit = newForm
        
    elif detail == 2:
        newForm = get_text(subsection, details[detail - 1], booking.forms.guestRegistration)
        booking.forms.guestRegistration = newForm
        
    elif detail == 3:
        newForm = get_text(subsection, details[detail - 1], booking.forms.balancePayment)
        booking.forms.balancePayment = newForm
        
    elif detail == 4:
        newForm = get_text(subsection, details[detail - 1], booking.forms.arrivalQuestionnaire)
        booking.forms.arrivalQuestionnaire = newForm
        
    elif detail == 5:
        booking.forms.guestRegistrationDone = True
    
    booking.update()

    return update_forms(subsection, booking)