import datetime

from apis.google.forms.form import GoogleForm
from default.booking.booking import Booking
from default.booking.functions import determine_price_of_extra
from default.database.database import Database
from default.database.functions import search_bookings
from default.dates import dates
from default.google.drive.functions import set_global_permissions
from default.google.forms.functions import get_form, get_form_file
from default.translator.functions import empty_translator_func
from forms.arrival.responses import ArrivalFormResponses
from forms.arrival.vars import (
    
    ARRIVAL_METHOD_SECTION,
    ARRIVAL_METHOD,
    
    FLIGHT_DETAILS_SECTION,
    INBOUND_FLIGHT_NUMBER,
    INBOUND_FLIGHT_TIME,
    OUTBOUND_FLIGHT_NUMBER,
    OUTBOUND_FLIGHT_TIME,
    CAR_HIRE,
    
    NON_FLIGHT_DETAILS_SECTION,
    ARRIVAL_TIME,
    ARRIVAL_COMMENTS,
    
    AIRPORT_TRANSFER_SECTION,
    AIRPORT_TRANSFER_OPTION,
    CHILD_SEATS,
    EXCESS_BAGGAGE,

    EXTRAS_SECTION,
    WELCOME_PACK_OPTION,
    MID_STAY_CLEAN_OPTION,
    COT_OPTION,
    HIGHCHAIR_OPTION,

)


def new_arrival_form(booking: Booking) -> GoogleForm:
    """
    Creates a new Google Form for guest arrival preparation questionnaire.

    This function retrieves an empty form file from Google Drive, copies it,
    and initializes a new Google Form with the specified title and sections
    for guest arrival details.

    Args:
        booking (Booking): The booking information for the guest.

    Returns:
        GoogleForm: The newly created Google Form object.
    """
    if booking.details.isOwner:
        driveFolder = 'Forms/Owner Arrival Preparation Questionnaire'
        formTitle = (
            f'Arrival Preparation for {booking.property.shortName} -'
            f'{booking.arrival.prettyDate}'
        )
    else:
        driveFolder = 'Forms/Guest Arrival Preparation Questionnaire'
        formTitle = (
            f'Arrival Preparation Questionnaire for '
            f'{booking.guest.name} - {booking.property.shortName}'
        )

    emptyFormFile = get_form_file('Empty Google Form', driveFolder)
    newFormFile = emptyFormFile.copy(copyName=formTitle)
    set_global_permissions(newFormFile)
    
    newForm = get_form(newFormFile.id)
    newForm.title = formTitle
    return newForm


def reset_arrival_form(booking: Booking, formSetter: callable) -> None:
    """
    Resets the guest arrival form for a booking by creating a new form.

    This function deletes the existing form associated with the booking and
    creates a new one, ensuring that the latest information is captured.

    Args:
        booking (Booking): The booking information for the guest.

    Returns:
        None
    """
    form = get_form(booking.forms.arrivalQuestionnaire)
    form.empty()
    formSetter(booking, form)


def set_arrival_section_of_form(
        form: GoogleForm, 
        translator: callable = empty_translator_func
) -> None:
    """
    Sets up the arrival section of the Google Form.
    
    This function adds a section to the form specifically for collecting
    arrival information from guests, including their arrival method and
    relevant details.
    
    Args:
        form (GoogleForm): The Google Form object to update.
    """

    form.newPageBreakItem(
        id=ARRIVAL_METHOD_SECTION,
        title = translator('ARRIVAL DAY'),
        description = translator(
            'Will you be flying into Faro Airport on check-in '
            'day or arriving by other means?')
    )
 
    choices = [
        GoogleForm.Option(
                        value=translator('1. Flight to FARO airport'), 
                        goToSectionId=FLIGHT_DETAILS_SECTION),
        GoogleForm.Option(
                        value=translator('2. Flight to LISBON airport'), 
                        goToSectionId=FLIGHT_DETAILS_SECTION),
        GoogleForm.Option(
                        value=translator('3. Bus to Albufeira station'), 
                        goToSectionId=NON_FLIGHT_DETAILS_SECTION),
        GoogleForm.Option(
                        value=translator('4. Train to Ferreiras (Albufeira) station'),
                        goToSectionId=NON_FLIGHT_DETAILS_SECTION),
        GoogleForm.Option(
                        value=translator('5. Driving from another location'), 
                        goToSectionId=NON_FLIGHT_DETAILS_SECTION),
        GoogleForm.Option(
                        value=translator('6. Other'), 
                        goToSectionId=NON_FLIGHT_DETAILS_SECTION),
    ]
    form.newChoiceQuestionItem(
        id=ARRIVAL_METHOD,
        title=translator('Please select:'),
        choiceType='RADIO',
        options=choices,
    )


def set_flight_details_section_of_form(
        form: GoogleForm, 
        booking: Booking, 
        translator: callable = empty_translator_func
) -> None:
    form.newPageBreakItem(
        id=FLIGHT_DETAILS_SECTION,
        title=translator('FLIGHT DETAILS')
    )
    form.newTextQuestionItem(
        id=INBOUND_FLIGHT_NUMBER,
        title=translator('Inbound Flight Number'),
        description=translator('\nPlease share the Flight Number (e.g. FR1234):'),
    )
    form.newTimeQuestionItem(
        id=INBOUND_FLIGHT_TIME,
        title=translator('Inbound Flight Landing Time'),
        description=translator(
            '\nPlease share the Flight Scheduled Landing Time (24 Hour Clock):',
        ),
    )
    form.newTextQuestionItem(
        id=OUTBOUND_FLIGHT_NUMBER,
        title=translator('Outbound Flight Number'),
        description=translator('\nPlease share the Flight Number (e.g. FR1234):'),
    )
    form.newTimeQuestionItem(
        id=OUTBOUND_FLIGHT_TIME,
        title=translator('Outbound Flight Take-off Time'),
        description=translator(
            '\nPlease share the Flight Scheduled Take-off Time (24 Hour Clock):',
        ),
    )
    form.newChoiceQuestionItem(
        id=CAR_HIRE,
        title=translator('Car Hire'),
        description=translator(
            '\nAre you planning to hire a car at the airport '
            'and drive to the accommodation?'),
        choiceType='RADIO',
        options=[
            GoogleForm.Option(
                value=translator('1. Yes'),
                goToSectionId=EXTRAS_SECTION
            ),
            GoogleForm.Option(
                value=translator('2. No'),
                goToSectionId=(
                    AIRPORT_TRANSFER_SECTION if not
                    booking.arrival.isImminent else
                    EXTRAS_SECTION
                )
            ),
        ]
    )


def set_non_flight_details_section_of_form(
        form: GoogleForm, 
        translator: callable = empty_translator_func
) -> None:
    form.newPageBreakItem(
        id=NON_FLIGHT_DETAILS_SECTION,
        title=translator('ARRIVAL IN ALBUFEIRA'),
        description=translator('Please let us know your expected arrival time in Albufeira:'),
    )
    form.newTimeQuestionItem(
        id=ARRIVAL_TIME,
        title=translator('Arrival Time'),
    )
    form.newTextQuestionItem(
        id=ARRIVAL_COMMENTS,
        title=translator('Additional Comments (Optional)'),
        shortAnswer=True,
        required=False,
    )


def set_airport_transfers_option_section_of_form(
        form: GoogleForm, 
        booking: Booking, 
        translator: callable = empty_translator_func
) -> None:
    """
    Sets up the airport transfers option section of the Google Form.

    This function adds a section to the form for collecting information about
    airport transfer options available to guests, including choices for inbound
    and outbound transfers, child seats, and excess baggage.

    Args:
        form (GoogleForm): The Google Form object to update.
        booking (Booking): The booking information for the guest.
    """
    if booking.arrival.isImminent:
        return
    
    form.newPageBreakItem(
        id=AIRPORT_TRANSFER_SECTION,
        title=translator('AIRPORT TRANSFERS OPTION'),
        description=translator(_airport_transfers_description()),
    )

    options = [
        GoogleForm.Option(
            value=translator('1. Inbound and Outbound Airport Transfers'),
            goToSectionId=EXTRAS_SECTION
        ),
        GoogleForm.Option(
            value=translator('2. Inbound Airport Transfer Only'),
            goToSectionId=EXTRAS_SECTION
        ),
        GoogleForm.Option(
            value=translator('3. Outbound Airport Transfer Only'),
            goToSectionId=EXTRAS_SECTION
        ),
        GoogleForm.Option(
            value=translator('4. None'),
            goToSectionId=EXTRAS_SECTION
        ),
    ]
    form.newChoiceQuestionItem(
        id=AIRPORT_TRANSFER_OPTION,
        title='Please select:',
        choiceType='RADIO',
        options=options,
    )
    form.newTextQuestionItem(
        id=CHILD_SEATS,
        title=translator('CHILD SEATS'),
        description=translator(
            '\nIf travelling with children under the age of 13, please '
            'specify their ages. Separate by commas (e.g. 5, 8, 12):'
        ),
        required=False,
    )
    form.newTextQuestionItem(
        id=EXCESS_BAGGAGE,
        title=translator('EXCESS BAGGAGE'),
        description=translator(
            '\nIf applicable, please describe any extra baggage '
            '(i.e. golf bags, additional large cases):'
        ),
        required=False,
    )


def set_extras_section_of_form(
        form: GoogleForm, 
        booking: Booking, 
        translator: callable = empty_translator_func
) -> None:
    """
    Sets up the extras section of the Google Form.
    
    This function adds a section to the form for collecting additional
    services and requests from guests, such as child seats, cots, high chairs,
    welcome packs, and mid-stay cleaning.
    
    Args:
        form (GoogleForm): The Google Form object to update.
    """
    form.newPageBreakItem(
        id=EXTRAS_SECTION,
        title=translator('OPTIONAL EXTRAS'),
        description=translator('If applicable, extras are paid for in cash at check-in.'),
    )
    
    if not booking.arrival.isVerySoon and booking.property.weClean:
        
        form.newChoiceQuestionItem(
            id=WELCOME_PACK_OPTION,
            title=translator('Welcome Pack of Food and Drink'),
            description=translator(
                '\nIncludes: loaf of Bread, jar of Jam, 6 medium-sized Eggs, tub of '
                'Butter, bottle of Wine, 6 bottles of Beer, carton of Milk, bottle of '
                'Water, carton of Orange Juice, Tea, Coffee.\n\nCost: €35.00'
            ),
            options=[
                GoogleForm.Option(value=translator('Yes, please!')),
            ],
            choiceType='CHECKBOX',
            required=False,
        )
    
    if booking.totalNights > 7 and booking.property.weClean:
    
        cost = 60.00
        if booking.property.specs.bedrooms > 1:
            cost += 15.00
        form.newChoiceQuestionItem(
            id=MID_STAY_CLEAN_OPTION,
            title=translator('Mid-stay Clean'),
            description=translator(
                '\nIncludes: fresh Linen and Towels, full dust down of apartment, '
                'vacuuming and washing of floors.'
                f'\n\nCost: €{cost:.2f}.'
            ),
            options=[
                GoogleForm.Option(value=translator('Yes, please!')),
            ],
            choiceType='CHECKBOX',
            required=False,
        )

    singleCost, combinedCost = 25.00, 35.00
    if booking.totalNights > 11:
        singleCost += 15.00
        combinedCost += 15.00

    form.newChoiceQuestionItem(
        id=COT_OPTION,
        title=translator('Children\'s Cot'),
        description=translator(
            f'\nCost: €{singleCost:.2f}.\n\nNote: if combined with '
            f'High Chair, cost is €{combinedCost:.2f}.'
        ),
        options=[
            GoogleForm.Option(value=translator('Yes, please!')),
        ],
        choiceType='CHECKBOX',
        required=False,
    )
    
    form.newChoiceQuestionItem(
        id=HIGHCHAIR_OPTION,
        title=translator('Children\'s High Chair'),
        description=translator(
            f'\nCost: €{singleCost:.2f}.\n\nNote: if combined with '
            f'Cot, cost is €{combinedCost:.2f}.'
        ),
        options=[
            GoogleForm.Option(value=translator('Yes, please!')),
        ],
        choiceType='CHECKBOX',
        required=False,
    )


def _airport_transfers_description() -> str:
    """
    Returns a description for the airport transfers option section of the form.
    
    This function provides information about the airport transfer options available
    to guests, including details about the service and its benefits.
    
    Returns:
        str: A description of the airport transfers option.
    """
    return (
        'FOR FLIGHTS TO AND FROM FARO AIRPORT WE CAN PROVIDE AIRPORT TRANSFERS'
        '\n\nInbound and Outbound'
        '\n\n\t1-4 people @ €84.00 total for 2 transfers'
        '\n\n\t5-8 people @ €114.00 total for 2 transfers'
        '\n\nInbound or Outbound Only'
        '\n\n\t1-4 people @ €45.00 total for 1 transfer'
        '\n\n\t5-8 people @ €60.00 total for 1 transfer'
        '\n\nNote: If a transfer takes place between 22:00 and 06:00 and additional '
        '€10.00 is added to the above prices.'
        '\n\nPayment is done in cash to the driver after the (first) drop-off.'
    )


def update_from_arrival_method_section(booking: Booking, responses: ArrivalFormResponses) -> Booking:
    """
    Updates arrival information in the booking based on form responses.
    
    This function determines the arrival method and updates the booking with
    appropriate details and timing based on whether the guest is arriving by
    flight, bus, train, or driving.
    
    Args:
        booking (Booking): The booking object to update.
        responses (ArrivalFormResponses): The form responses containing arrival
            information.
    
    Returns:
        Booking: The updated booking object.
    """
    if responses.arrivalIsFlight:
        booking.arrival.isFaro = responses.flightIsFaro
        booking.departure.isFaro = responses.flightIsFaro
        booking.arrival.flightNumber = responses.inboundFlightNumber
        booking.arrival.time = responses.inboundFlightTime
        booking.departure.flightNumber = responses.outboundFlightNumber
        booking.departure.time = responses.outboundFlightTime
        booking.arrival.details = 'Hiring a car' if responses.carHire else None
    
    else:
        details, time = _get_non_flight_arrival_details(responses.arrival, responses)    
        booking.arrival.details = details
        booking.arrival.time = time
    
    return booking


def _get_non_flight_arrival_details(
    arrival: str, 
    responses: ArrivalFormResponses) -> tuple[str, datetime.time]:
    """
    Updates arrival details and time for bus or train transportation.
    
    This function processes bus or train arrival information, calculates
    the arrival time with a 30-minute buffer, and formats the details string.
    
    Args:
        arrival (str): The arrival method description.
        responses (ArrivalFormResponses): The form responses containing
            bus/train timing information.
    
    Returns:
        tuple[str, datetime.time]: A tuple containing the formatted arrival
            details and the calculated arrival time.
    """
    arrivalTime = responses.arrivalTime
    if arrivalTime < datetime.time(6, 0):
        arrivalTime = dates.calculate(time=arrivalTime, hours=12)
    prettyTime = dates.prettyTime(arrivalTime)
    comments = responses.arrivalComments

    if '3. ' in arrival:
        details = f'Bus to Albufeira station arriving @ {prettyTime}'
        time = dates.calculate(
            time=arrivalTime, 
            minutes=30
        )
        
    elif '4. ' in arrival:
        details = f'Train to Ferreiras station arriving @ {prettyTime}'
        time = dates.calculate(
            time=arrivalTime, 
            minutes=40
        )
    
    elif '5. ' in arrival:
        details = f'Driving to Albufeira ETA @ {prettyTime}'
        time = arrivalTime

    else:
        details = f'ETA @ {prettyTime}'
        time = arrivalTime

    if comments:
            details += f' ({comments})'
    
    return details, time


def update_from_extras_section(
    booking: Booking, 
    responses: ArrivalFormResponses) -> Booking:
    """
    Updates booking extras based on arrival form responses.
    
    This function processes additional services and requests such as airport
    transfers, child seats, equipment rentals, and special comments.
    
    Args:
        booking (Booking): The booking object to update.
        responses (ArrivalFormResponses): The form responses containing
            extra services information.
        selfEmail (list | None): Optional list to collect bookings with
            comments for email notifications. Defaults to None.
    
    Returns:
        Booking: The updated booking object with extras information.
    """
    extras = booking.extras
  
    extras.airportTransfers = responses.airportTransfers
    extras.airportTransferInboundOnly = responses.airportTransferInboundOnly
    extras.airportTransferOutboundOnly = responses.airportTransferOutboundOnly
    extras.childSeats = responses.childSeats
    extras.excessBaggage = responses.excessBaggage
    extras.cot = responses.cot
    extras.highChair = responses.highChair    
    extras.welcomePack = responses.welcomePack    
    extras.midStayClean = responses.midStayClean
    extras.ownerIsPaying = _determine_who_pays(booking)

    return booking


def get_arrival_form_booking(database: Database, formId: str) -> Booking | None:
    """
    Retrieves the arrival booking with the specified ID from the database.

    Args:
        database: The database connection object.
        booking_id: The ID of the booking to retrieve.

    Returns:
        Booking: The booking object if found, None otherwise.
    """
    search = search_bookings(database)

    select = search.guests.select()
    select.firstName()
    select.lastName()

    select = search.properties.select()
    select.shortName()

    select = search.departures.select()
    select.date()
    
    where = search.forms.where()
    where.arrivalQuestionnaire().isEqualTo(formId)
    
    return search.fetchone()


def _determine_who_pays(booking: Booking) -> bool:
    """
    Determine who is paying for the extras in the booking.
    
    Args:
        booking (Booking): The booking object to check.
    
    Returns:
        bool: True if the owner is paying, False otherwise.
    """
    return booking.details.isOwner and booking.property.shortName == 'A24'