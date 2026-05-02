from apis.google.forms.form import GoogleForm
from default.booking.booking import Booking
from default.dates import dates
from default.google.drive.functions import set_global_permissions
from default.google.forms.functions import (
    get_form,
    get_form_file,
    get_form_responses
)
from default.property.property import Property
from default.settings import (
    DEFAULT_ACCOUNT,
    TEST
)
from default.translator.functions import translator as _translator
from forms.registration.responses import GuestRegistrationFormResponses
from utils import (
    convert_to_base_64,
    gen_hex,
    logerror,
    sublog
)
from web.xml import XMLTreeBuilder
from zeep import Client

_COUNTRIES: list[str] | None = None
_DRIVE_PATH: str = 'Forms/Guest Registration'
_EMPTY_FORM: str = 'Empty Google Form'


def _set_countries() -> list[str]:
    """
    Initializes the global _COUNTRIES variable with a sorted list of country 
    names and their alpha-3 codes.
    
    This function uses the pycountries library to retrieve country data.
    
    Returns:
        list[str]: A sorted list of country names with their alpha-3 codes.
    """
    from pycountries import Country
    global _COUNTRIES
    _COUNTRIES = sorted([f'{ctry.name} - {ctry.alpha_3}' for ctry in list(Country)])
    return _COUNTRIES


def new_guest_registration_form(booking: Booking) -> GoogleForm:
    """
    Creates a new guest registration form for a given lead guest and property name, 
    with the specified total number of guests.
    
    Args:
        leadGuest (str): The name of the lead guest.
        propertyName (str): The name of the property.
        totalGuests (int): The total number of guests to register.
  
    Returns:
        GoogleForm: The newly created guest registration form.
    
    Raises:
        ValueError: If totalGuests is less than 1.
    """
    if not _COUNTRIES:
        _set_countries()

    translator = _translator(booking.guest.preferredLanguage)

    print(booking)

    title = translator(f'Guest Registration Form for {booking.guest.name} to {booking.property.name}')
    emptyFormFile = get_form_file(name=_EMPTY_FORM, drivePath=_DRIVE_PATH)
    newFormFile = emptyFormFile.copy(copyName=title)
    set_global_permissions(file=newFormFile)
    
    form = get_form(id=newFormFile.id)
    form.title = title
    form.description = translator(_registration_description(booking.details.totalGuests))
 
    _set_portuguese_nif_question(form, translator)

    for guest in range(1, booking.details.totalGuests + 1):
        form.newPageBreakItem(
                            id=gen_hex(guest, 0), 
                            title=translator(f'Registration for Group - Guest {guest}'))
        _set_guest_questions(form, translator, guest)
    
    form.update(sleep=1.5)
    return form


def get_guest_registration_form_responses(id: str) -> GuestRegistrationFormResponses:
    """
    Retrieves the responses from a guest registration form using its ID.
    
    Args:
        id (str): The ID of the guest registration form.
    
    Returns:
        GuestRegistrationFormResponses: An object containing the form responses.
    """
    responses = get_form_responses(id=id, objectType=GuestRegistrationFormResponses)
    return responses.latest


def _set_portuguese_nif_question(form: GoogleForm, translator: callable) -> None:
    """
    Sets a question for the Portuguese NIF (Número de Identificação Fiscal) 
    in the guest registration form.
    
    Args:
        form (GoogleForm): The GoogleForm object to set the question on.
    
    Raises:
        ValueError: If the form is None.
    """
    if not form:
        raise ValueError('Form cannot be None.')
    
    yes = GoogleForm.Option(value='Yes')
    yes.goToAction = 'SUBMIT_FORM'
    no = GoogleForm.Option(value='No')
    no.goToAction = 'NEXT_SECTION'
    
    form.newChoiceQuestionItem(
        id=gen_hex(0, 1), 
        title=translator('PORTUGUESE TAX NUMBER (NIF)'), 
        description=(
            translator('Do you have a Portuguese Tax Number (Número de Identificação '
            'Fiscal)?')),
        choiceType='RADIO',
        options=[yes, no])
    
    form.newTextQuestionItem(
        id=gen_hex(0, 2),
        title='',
        description=(
            translator('If you said YES on the previous question please ENTER your '
            'Portuguese NIF (Número de Identificação Fiscal)')),
        required=False,
    )


def _set_guest_questions(form: GoogleForm, translator: callable, num: int) -> None:
    """
    Sets the questions for a guest registration form, including personal 
    details and identification information.
    
    Args:
        form (GoogleForm): The GoogleForm object to set the questions on.
        num (int): The guest number for which the questions are being set.
        
    Raises:
        ValueError: If num is less than 1.
    """
    if num < 1:
        raise ValueError('Guest number must be at least 1.')
    
    form.newTextQuestionItem(
        id=gen_hex(num, '1'), title=translator('FIRST NAME'))
    form.newTextQuestionItem(
        id=gen_hex(num, '2'), title=translator('LAST NAME'))
    form.newDateQuestionItem(
        id=gen_hex(num, '3'), title=translator('DATE OF BIRTH'))
    form.newChoiceQuestionItem(
        id=gen_hex(num, '4'), title=translator('PLACE OF BIRTH'), options=_COUNTRIES)
    form.newChoiceQuestionItem(
        id=gen_hex(num, '5'), title=translator('NATIONALITY'), options=_COUNTRIES)
    form.newChoiceQuestionItem(
        id=gen_hex(num, '6'), title=translator('COUNTRY OF RESIDENCE'), options=_COUNTRIES)
    form.newChoiceQuestionItem(
        id=gen_hex(num, '7'), title=translator('TYPE OF IDENTIFICATION'), options=[
            translator('ID Card'), translator('Passport')])
    form.newTextQuestionItem(
        id=gen_hex(num, '8'), title=translator('ID CARD/PASSPORT NUMBER'))
    form.newChoiceQuestionItem(
        id=gen_hex(num, '9'), title=translator('ID CARD/PASSPORT ISSUER'), options=_COUNTRIES)


def _registration_description(totalGuests: int) -> str:
    """
    Generates the main description for the guest registration form.
    
    Args:
        totalGuests (int): The total number of guests to register.
    
    Returns:
        str: The main description text for the form.
    """
    return (
        f'\nThis form has been prepared for {totalGuests} GUESTS. We ask that you, '
        'as the lead guest, insert your details first. The order after that does '
        'not matter.\n\nIF you have a *Portuguese Tax Number (NIF: Número de '
        'Identificação Fiscal), only that will be needed*.'
    )


def send_responses_to_siba_sef_pt(
    responses: GuestRegistrationFormResponses, 
    guests: int = 1, 
    booking: Booking | None = None, 
    done: int = 0) -> None:
    """
    Sends guest registration responses to the SIBA SEF PT service.
    This function constructs an XML structure with the guest details and 
    sends it to the SEF service.
    
    Args:
        responses (GuestRegistrationFormResponses): The form responses 
            containing guest details.
        guests (int): The number of guests to register. Defaults to 1.
        booking (Booking | None): The booking object containing details 
            about the stay. Defaults to None.
        done (int): The number of guests already processed. Defaults to 0.

    Returns:
        None
    """
    if booking is not None and done == booking.details.totalGuests:
        return
    
    tree = XMLTreeBuilder(name='MovimentoBAL', xmlns="http://sef.pt/BAws")
    _set_property_table_for_siba_sef_pt(tree, booking.property)
    
    for guest in range(1, guests + 1):
        responses.guest = guest
        _set_guest_table_for_siba_sef_pt(tree, responses, booking)
    
    _set_send_details_table_for_sef_pt(tree)
    boletins = tree.get()
    boletins = convert_to_base_64(boletins)
    
    client = Client(_get_sef_send_address())
    (
        unidadeHoteleira, 
        estabelecimento, 
        chaveDeAutenticacao
                            ) = _get_property_sef_login_details(booking.property)
    response = client.service.EntregaBoletinsAlojamento(
        unidadeHoteleira, 
        estabelecimento, 
        chaveDeAutenticacao, 
        boletins)
    
    if str(response) == '0':
        sublog(
            f'Successfully sent {guests} guest registrations to SIBA SEF PT '
            f'for {booking.guest.lastName} in {booking.property.shortName}')
    else:
        logerror(
            f'Error sending guest registration responses to SIBA SEF PT for '
            f'{booking.guest.lastName} in {booking.property.shortName}: '
            f'{response}')


def _set_property_table_for_siba_sef_pt(tree: XMLTreeBuilder, 
                                        property: Property) -> None:
    """
    Sets the property details in the SIBA SEF PT XML structure.
    This includes the hotel unit code, establishment, name, and address details.

    Args:
        tree (XMLTreeBuilder): The XML tree builder to construct the XML 
            structure.
        property (Property): The property object containing the details to be 
            set.

    Returns:
        None
    """
    unidade = tree.newBranch('Unidade_Hoteleira')
    unidadeHoteleira, estabelecimento, _ = _get_property_sef_login_details(property)
    unidade.newBranch('Codigo_Unidade_Hoteleira', unidadeHoteleira)
    unidade.newBranch('Estabelecimento', estabelecimento)
    unidade.newBranch('Nome', property.name)
    unidade.newBranch('Abreviatura', property.shortName)
    morada, localidade, codigoPostal, zonaPostal = _get_property_address_details(property)
    unidade.newBranch('Morada', morada)
    unidade.newBranch('Localidade', localidade)
    unidade.newBranch('Codigo_Postal', codigoPostal)
    unidade.newBranch('Zona_Postal', zonaPostal)
    unidade.newBranch('Telefone', DEFAULT_ACCOUNT.noPrefix().phoneNumber)
    unidade.newBranch('Fax', '')
    unidade.newBranch('Nome_Contacto', DEFAULT_ACCOUNT.name)
    unidade.newBranch('Email_Contacto', DEFAULT_ACCOUNT.emailAddress)


def _set_guest_table_for_siba_sef_pt(
    tree: XMLTreeBuilder, 
    form: GuestRegistrationFormResponses, 
    booking: Booking
) -> None:
    """
    Sets the guest details in the SIBA SEF PT XML structure.
    This includes personal details such as name.

    Args:
        tree (XMLTreeBuilder): The XML tree builder to construct the XML structure.
        form (GuestRegistrationFormResponses): The form responses containing guest details.
        booking (Booking): The booking object containing details about the stay.

    Returns:
        None
    """
    bulletin = tree.newBranch('Boletim_Alojamento')
    bulletin.newBranch('Apelido', form.lastName)
    bulletin.newBranch('Nome', form.firstName)
    bulletin.newBranch('Nacionalidade', form.nationalityForSEF)
    bulletin.newBranch('Data_Nascimento', form.dateOfBirthForSEF)
    bulletin.newBranch('Local_Nascimento', '')
    bulletin.newBranch('Documento_Identificacao', form.identificationNumber[:16])
    bulletin.newBranch('Pais_Emissor_Documento', form.identificationIssuerForSEF)
    bulletin.newBranch('Tipo_Documento', form.identificationTypeForSEF)
    bulletin.newBranch('Data_Entrada', dates.makeDatetime(booking.arrival.date).isoformat())
    bulletin.newBranch('Data_Saida', dates.makeDatetime(booking.departure.date).isoformat())
    bulletin.newBranch('Pais_Residencia_Origem', form.countryOfResidenceForSEF)
    bulletin.newBranch('Local_Residencia_Origem', '')


def _set_send_details_table_for_sef_pt(tree: XMLTreeBuilder) -> None:
    """
    Sets the details for the send operation in the SIBA SEF PT XML structure.
    This includes the file number and the date of the movement.

    Args:
        tree (XMLTreeBuilder): The XML tree builder to construct the XML 
            structure.

    Returns:
        None
    """
    send = tree.newBranch(name='Envio')
    fileNum = f'{dates.year()}{dates.month()}{dates.day()}'
    send.newBranch('Numero_Ficheiro', fileNum)
    send.newBranch('Data_Movimento', f'{dates.now().isoformat()}')


def _get_property_address_details(property: Property) -> tuple[str, str, str, str]:
    """
    Extracts the address details from a Property object.

    The address is expected to be in the format "Street Address, 
    Postal Code Locality". The function splits the address into its components:
    - morada: The street address without the postal code.
    - localidade: The locality (city or town).
    - codigoPostal: The postal code.
    - zonaPostal: The postal zone.
    
    Args:
        property (Property): The property object containing the address.
  
    Returns:
        tuple[str, str, str, str]: A tuple containing morada, localidade, 
            codigoPostal, and zonaPostal.
    """
    address = property.address.split(', ')
    morada = ', '.join(address[:-1])
    codigoLocalidade = address[-1].split()
    localidade = codigoLocalidade[-1]
    codigoPostal, zonaPostal = codigoLocalidade[0].split('-')
    return morada, localidade, codigoPostal, zonaPostal


def _get_property_sef_login_details(property: Property) -> tuple[str, str, str]:
    """
    Retrieves the SEF login details for a given property.
    This function returns the hotel unit code, establishment, and authentication key.
    If the TEST flag is set, it returns dummy values for testing purposes.
    
    Args:
        property (Property): The property object containing SEF details.
    
    Returns:
        tuple[str, str, str]: A tuple containing unidadeHoteleira, 
            estabelecimento, and chaveDeAutenticacao.
    """
    if TEST:
        return "121212121", '0', '999999999'
    return (
        property.sefDetails.unidadeHoteleira,
        property.sefDetails.estabelecimento,
        property.sefDetails.chaveDeAutenticacao
    ) 


def _get_sef_send_address() -> str:
    """
    Returns the URL for the SEF send service based on the TEST flag.
    If TEST is True, it returns the development URL; otherwise, it returns 
    the production URL.
    
    Returns:
        str: The URL for the SEF send service.
    """
    if TEST:
        return 'https://siba.ssi.gov.pt/bawsdev/boletinsalojamento.asmx?wsdl'
    return 'https://siba.ssi.gov.pt/baws/boletinsalojamento.asmx?wsdl'