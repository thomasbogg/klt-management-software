from apis.google.drives.directory import GoogleDriveDirectory
from apis.google.forms.form import GoogleForm
from default.booking.booking import Booking
from default.database.database import Database
from default.google.drive.functions import (
    get_klt_management_directory_on_drive, 
)
from default.google.forms.functions import get_form_responses as _get_form_responses
from default.guest.guest import Guest
from forms.arrival.owner.responses import OwnerArrivalFormResponses
from utils import logwarning
from forms.arrival.functions import (
    new_arrival_form,
    set_arrival_section_of_form,
    set_flight_details_section_of_form,
    set_non_flight_details_section_of_form,
    set_airport_transfers_option_section_of_form,
    set_extras_section_of_form,
)
from forms.arrival.vars import (
    GUEST_DETAILS_SECTION,
    GUEST_FIRST_NAME,
    GUEST_LAST_NAME,
    GUEST_EMAIL_ADDRESS,
    GUEST_PHONE_NUMBER,
    TOTAL_ADULTS,
    TOTAL_CHILDREN,
    TOTAL_BABIES,
    CLEAN_OPTION,
    IS_FOR_OWNER,
    MEET_GREET_SECTION,
    MEET_GREET_OPTION,
    ARRIVAL_METHOD_SECTION,
    OWNER_COMMENTS_SECTION,
    OWNER_COMMENTS,
)


def set_owner_arrival_form(booking: Booking, form: GoogleForm = None) -> str:
    """
    Creates a new Google Form for owner arrival preparation questionnaire.

    This function initializes a new form with sections for arrival details,
    flight details, airport transfers, and extras. It sets up the form with
    appropriate questions and options for owners to fill out.

    Args:
        booking (Booking): The booking information for the property.
        form: Optional existing form to modify.
        
    Returns:
        The ID of the created or modified Google Form.
    """
    if form is None:
        form = new_arrival_form(booking)
    
    form.emailCollectionType = 'DO_NOT_COLLECT'
    form.description = _arrival_form_description()

    _set_guest_numbers(form, booking)
    _set_clean_and_guest_type(form)
    _set_meet_greet_section(form)
    _set_guest_details_section(form)

    set_arrival_section_of_form(form)
    set_flight_details_section_of_form(form, booking)
    set_airport_transfers_option_section_of_form(form, booking)
    set_non_flight_details_section_of_form(form)
    set_extras_section_of_form(form, booking)

    _set_owner_comments_section(form)

    form.update()
    form.publish()

    booking.forms.arrivalQuestionnaire = form.id
    booking.update()
    
    return form.id


def _set_guest_numbers(form: GoogleForm, booking: Booking) -> None:
    """
    Sets the number of guests in the form based on booking details.

    Args:
        form: The Google Form to modify.
        booking: The booking information for the property.
    
    Returns:
        None
    """
    capacity = booking.property.specs.bedrooms * 2 + 2
    guests = [GoogleForm.Option(value=str(i)) for i in range(capacity + 1)]
    totalAdults: list[int] = guests[1:]
    totalChildren: list[int] = guests[:-1]
    totalBabies: list[int] = guests[:-1]

    form.newChoiceQuestionItem(
        id=TOTAL_ADULTS,
        title='Total Adults',
        options=totalAdults,
        required=True,
    )
    form.newChoiceQuestionItem(
        id=TOTAL_CHILDREN,
        title='Total Children',
        options=totalChildren,
        required=False,
    )
    form.newChoiceQuestionItem(
        id=TOTAL_BABIES,
        title='Total Babies',
        options=totalBabies,
        required=False,
    )


def _set_clean_and_guest_type(form: GoogleForm) -> None:
    """
    Sets the cleaning and guest type options in the form.
    
    Args:
        form: The Google Form to modify.

    Returns:
        None
    """
    form.newChoiceQuestionItem(
        id=CLEAN_OPTION,
        title='Cleaning Required After Departure?',
        choiceType='RADIO',
        options=[
            GoogleForm.Option(value='1. Yes, please!'),
            GoogleForm.Option(value='2. No, thank you.'),
        ],
        required=True,
    )

    form.newChoiceQuestionItem(
        id=IS_FOR_OWNER,
        title='Is this booking for you?',
        choiceType='RADIO',
        options=[
            GoogleForm.Option(
                            value='1. Yes, this booking is for me!', 
                            goToSectionId=ARRIVAL_METHOD_SECTION),
            GoogleForm.Option(
                            value='2. No, I have booked these dates for someone else.', 
                            goToSectionId=MEET_GREET_SECTION),
        ],
        required=True,
    )


def _set_meet_greet_section(form: GoogleForm) -> None:
    """
    Sets the meet and greet section in the form.
    
    Args:
        form: The Google Form to modify.

    Returns:
        None
    """
    form.newPageBreakItem(
        id=MEET_GREET_SECTION,
        title='MEET & GREET',
        description=
            'As you selected that this booking is for someone else, please let ' \
            'us know if we need to meet them on arrival day.'
    )

    form.newChoiceQuestionItem(
        id=MEET_GREET_OPTION,
        title='Please select:',
        choiceType='RADIO',
        options=[
            GoogleForm.Option(
                value=
                    '1. Yes. I would like someone to meet and greet the guests and ' \
                    'hand over the keys.'),
            GoogleForm.Option(
                value=
                    '2. No. The guests will have keys so no meet and greet is ' \
                    'required.'),
        ],
        required=True,
    )


def _set_guest_details_section(form: GoogleForm) -> None:
    """
    Sets the guest details section in the form.
    
    Args:
        form: The Google Form to modify.
        booking: The booking information for the property.

    Returns:
        None
    """
    form.newPageBreakItem(
        id=GUEST_DETAILS_SECTION,
        title='GUEST DETAILS',
        description=
            f'For us to be able to coordinate successfully with your guests, we ' \
            'need their contact details. Please provide what you can.'
    )
    form.newTextQuestionItem(
        id=GUEST_FIRST_NAME,
        title='Lead Guest First Name',
    )
    form.newTextQuestionItem(
        id=GUEST_LAST_NAME,
        title='Lead Guest Last Name',
    )
    form.newTextQuestionItem(
        id=GUEST_EMAIL_ADDRESS,
        title='Lead Guest Email Address',
        description=
            '\nIf an email provide address is provided, we will contact the guests ' \
            'directly with arrival instructions as well as final day reminders. This ' \
            'will relieve you of the trouble of communicating with them yourself.'
            '\n\nPlease let your guests know that they will be contacted from ' \
            'thomas@algarvebeachapartments.com .',
    )
    form.newTextQuestionItem(
        id=GUEST_PHONE_NUMBER,
        title='Guest Phone Number',
        description=
            'Please include Country Dialing Code (e.g. +1, +44, +351): ' \
            'https://countrycode.org/',
    )


def _set_owner_comments_section(form: GoogleForm) -> None:
    """
    Sets the owner comments section in the form.
    
    Args:
        form: The Google Form to modify.

    Returns:
        None
    """
    form.newPageBreakItem(
        id=OWNER_COMMENTS_SECTION,
        title='ADDITIONAL COMMENTS (OPTIONAL)',
        description=
            'Please add any additional comments you wish us to acknowledge regarding ' \
            'this booking.'
    )
    form.newTextQuestionItem(
        id=OWNER_COMMENTS,
        title='Type here:',
        required=False,
    )


def _arrival_form_description() -> str:
    """
    Returns the description for the owner arrival form.
    
    This description provides context and instructions for filling out the form.
    
    Returns:
        A string containing the form description.
    """
    return (
        "Thank you very much for taking the time to complete this form. Every detail "
        "you share helps us achieve our mission of delivering the highest standards of "
        "care.\n\n"
        "The form follows a certain flow depending on how you answer. For instance, "
        "if this booking is not for you and your guests require a meet and greet on "
        "arrival day, we ask that an email address and phone number be provided for "
        "optimal coordination. Otherwise, you will not be asked to fill in this "
        "particular section and be directed straight to your arrival day plans.\n\n"
        "The final section will give you a chance to add any additional comments you "
        "wish us to acknowledge regarding the booking.\n\n"
        "Thank you again!"
    )


def get_owner_arrival_forms_on_drive() -> GoogleDriveDirectory:
    """
    Retrieves the Google Drive directory for owner arrival forms.
    
    Returns:
        The Google Drive directory containing owner arrival questionnaires.
    """
    drivePath: str = 'Forms/Owner Arrival Preparation Questionnaire'
    driveDirectory: GoogleDriveDirectory = get_klt_management_directory_on_drive(drivePath)
    return driveDirectory


def generate_arrival_questionnaire_title(booking: Booking) -> str:
    """
    Generates the title for the owner arrival questionnaire based on booking details.
    
    Args:
        booking: The booking information for the property and arrival.
        
    Returns:
        A formatted title string for the questionnaire.
    """
    return f'Arrival Preparation for {booking.property.shortName} - {booking.arrival.prettyDate}'


def get_form_responses(formId: str) -> OwnerArrivalFormResponses:
    """
    Retrieves and parses responses from an owner arrival form.
    
    Args:
        formId: The ID of the Google Form to retrieve responses from.
        
    Returns:
        Parsed owner arrival form responses.
    """
        
    responses: None | OwnerArrivalFormResponses = _get_form_responses(
                                                                formId, 
                                                                objectType=OwnerArrivalFormResponses)
    if not responses:
        return None
    if responses.hasMany:
        logwarning(
            f'Found multiple responses for form {formId}. Using the latest response only.')
    return responses.latest


def update_from_booking_details_section(booking: Booking, responses: OwnerArrivalFormResponses) -> Booking:
    """
    Updates booking details based on owner form responses.
    
    Args:
        booking: The booking to update.
        responses: The parsed form responses.
        
    Returns:
        The updated booking object.
    """
    booking.details.adults = responses.adults
    booking.details.children = responses.children
    booking.details.babies = responses.babies
    booking.departure.clean = responses.clean

    if not responses.selfBooking: 
        booking.arrival.meetGreet = responses.meetGreet
    else:
        booking.arrival.meetGreet = False
    return booking


def update_from_guest_details_section(
        database: Database, 
        booking: Booking, 
        responses: OwnerArrivalFormResponses,
) -> Booking:
    """
    Updates the guest information in the booking when the owner is not the guest.
    
    Args:
        database: The database connection.
        booking: The booking to update.
        responses: The parsed form responses.
        
    Returns:
        The updated booking object with guest information.
    """
    booking.guest = Guest(database)    

    booking.guest.firstName = responses.firstName.capitalize()
    booking.guest.lastName = responses.lastName.capitalize()
    email = responses.email
    email = email.replace(' ', '')
    booking.guest.email = email
    booking.guest.phone = responses.phone
  
    guestId: int = booking.guest.insert()
    booking.details.guestId = guestId
    return booking


def update_from_owner_comments_section(
        booking: Booking, 
        responses: OwnerArrivalFormResponses,
        selfEmail: list | None = None
) -> Booking:
    """
    Updates the booking with comments from the owner.
    
    Args:
        booking: The booking to update.
        responses: The parsed form responses.
        selfEmail: Optional list to append comments to for email advising.
        
    Returns:
        The updated booking object with owner comments.
    """
    comments = responses.comments
    if comments:
        booking.extras.otherRequests = comments
        if selfEmail is not None:
            selfEmail.append((booking, comments))
    return booking