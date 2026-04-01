from apis.google.drives.directory import GoogleDriveDirectory
from default.booking.booking import Booking
from default.google.drive.functions import (
    get_klt_management_directory_on_drive,
)
from default.google.forms.functions import get_form_responses as _get_form_responses
from forms.arrival.functions import (
    new_arrival_form,
    set_arrival_section_of_form,
    set_flight_details_section_of_form,
    set_airport_transfers_option_section_of_form,
    set_non_flight_details_section_of_form,
    set_extras_section_of_form,
)
from forms.arrival.vars import GUEST_PHONE_NUMBER
from forms.arrival.guest.responses import GuestArrivalFormResponses
from default.translator.functions import translator as _translator
from utils import (
    logwarning,
)

def get_guest_arrival_forms_on_drive() -> GoogleDriveDirectory:
    """
    Retrieves the Google Drive directory for guest arrival forms.
    
    Returns:
        The Google Drive directory containing guest arrival questionnaires.
    """
    drivePath: str = 'Forms/Guest Arrival Preparation Questionnaire'
    driveDirectory: GoogleDriveDirectory = get_klt_management_directory_on_drive(drivePath)
    return driveDirectory


def generate_arrival_questionnaire_title(booking: Booking) -> str:
    """
    Generates the title for the arrival questionnaire based on booking details.
    
    Args:
        booking: The booking information for the guest.
        
    Returns:
        A formatted title string for the questionnaire.
    """
    title: str = f'Arrival Preparation Questionnaire for {booking.guest.name} - {booking.property.shortName}'
    return title


def set_guest_arrival_form(booking: Booking, form = None) -> str:
    """
    Creates a new Google Form for guest arrival preparation questionnaire.

    This function initializes a new form with sections for arrival details,
    flight details, airport transfers, and extras. It sets up the form with
    appropriate questions and options for guests to fill out.

    Args:
        booking (Booking): The booking information for the guest.

    Returns:
        None
    """
    translator = _translator(booking.guest.preferredLanguage)
    if not form:
        form = new_arrival_form(booking)
        form.title = translator(form.title)

    form.emailCollectionType = 'RESPONDER_INPUT'
    form.description = translator(_arrival_form_description())

    form.newTextQuestionItem(
        id=GUEST_PHONE_NUMBER,
        title=translator('Holiday Phone Number'),
        description=translator(
            'Please include Country Dialing Code (e.g. +1, +44, +351): ' \
            'https://countrycode.org/'
        )
    )

    set_arrival_section_of_form(form, translator=translator)
    set_flight_details_section_of_form(form, booking, translator=translator)
    set_airport_transfers_option_section_of_form(form, booking, translator=translator)
    set_non_flight_details_section_of_form(form, translator=translator)
    set_extras_section_of_form(form, booking, translator=translator)

    form.update()
    form.publish()

    booking.forms.arrivalQuestionnaire = form.id
    booking.update()
    
    return form.id


def get_form_responses(formId: str) -> GuestArrivalFormResponses:
    """
    Retrieves and parses responses from a guest arrival form.
    
    Args:
        formId: The ID of the Google Form to retrieve responses from.
        
    Returns:
        Parsed guest arrival form responses.
    """
    responses: None | GuestArrivalFormResponses = _get_form_responses(
                                                                formId, 
                                                                objectType=GuestArrivalFormResponses)
    if not responses:
        return None
    if responses.hasMany:
        logwarning(
            f'Found multiple responses for form {formId}. Using the latest response only.')
    return responses.latest


def update_from_guest_details_section(
        booking: Booking, 
        responses: GuestArrivalFormResponses
) -> Booking:
    """
    Updates guest information in the booking based on arrival form responses.

    This function updates the guest's email and phone number if provided in the
    responses and if they meet certain criteria.

    Args:
        booking (Booking): The booking object to update.
        responses (GuestArrivalFormResponses): The form responses containing
            guest information.

    Returns:
        Booking: The updated booking object.
    """
    email = responses.email
    if '@' in responses.email:
        email = email.replace(' ', '')
        booking.guest.email = email

    databasePhone = booking.guest.phone
    if '+' in responses.phone or responses.phone.startswith('00') or not databasePhone:
        if len(responses.phone) > 5:
            booking.guest.phone = responses.phone

    return booking


def _arrival_form_description() -> str:
    """
    Returns a description for the arrival preparation questionnaire form.
    
    This function provides a brief overview of the form's purpose and what
    information it collects from guests regarding their arrival details.
    
    Returns:
        str: A description of the arrival preparation questionnaire.
    """
    return  (
        'First of all, thank you very much for taking the time to complete this '
        'form. Every detail you share helps us achieve our mission of delivering '
        'the highest standards of guest care.' 
        '\n\nAs experienced and dedicated managers of holidays, we aim to be present '
        'for you from the moment you arrive to the moment you leave. The questions '
        'below will not only give us a better understanding of your arrival day '
        'plans, but a good idea of any additional services we may be able to provide '
        'during your stay, as well as how to make departure day as relaxed as '
        'possible for you.'
        '\n\nYour cooperation is really appreciated. We look '
        'forward to welcoming you to Albufeira!'
    )