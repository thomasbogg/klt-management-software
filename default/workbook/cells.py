from default.booking.booking import Booking
from default.booking.functions import (
    determine_commission,
    determine_commission_after_IVA,
    determine_klt_commission,
    determine_management_fee,
    determine_need_for_invoice,
    determine_non_klt_commission,
    determine_owner_invoice,
    determine_owner_payment,
    determine_platform_fee,
    determine_platform_fee_IVA,
    determine_platform_fee_with_IVA,
    determine_total_to_be_receipted
)
from workbooks.dates import WorksheetDates
from workbooks.stylesheet import Stylesheet
from workbooks.worksheet import Worksheet


#######################################################
# MAIN CELL SETTERS
#######################################################

def set_cell(worksheet: Worksheet, stylesheet=Stylesheet, **kwargs) -> Worksheet:
    """
    Set cell properties and styles for a worksheet cell.
    
    Args:
        worksheet: The worksheet to modify.
        stylesheet: The stylesheet class to instantiate for styling.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    styles = stylesheet()

    split = kwargs.pop('split', False)
    if split:
        return set_split_cells(worksheet, **kwargs)
    
    for key, value in kwargs.items():
        if hasattr(worksheet.cell, key):
            setattr(worksheet.cell, key, value)
        elif hasattr(worksheet.row, key):
            setattr(worksheet.row, key, value)
        elif hasattr(worksheet.column, key):
            setattr(worksheet.column, key, value)
        elif hasattr(styles, key):
            setattr(styles, key, value)

    worksheet.cell.styles = styles

    #try:
    #    if kwargs.get('isDeparture', False) and kwargs.get('color', '000000') == '00FF0000':
    #        print('\n\n', worksheet.cell.value, worksheet.name, worksheet.row.number)  # Debug print statement
    #except Exception as e:
    #    print(f"Error printing debug info: {e}")
    return worksheet


def set_split_cells(worksheet: Worksheet, **kwargs) -> Worksheet:
    """
    Set properties for a series of cells, splitting a value among them.
    
    Args:
        worksheet: The worksheet to modify.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    value = kwargs.get('value', None)
    for i, fraction in enumerate(worksheet.fractions):
        worksheet.column.number = worksheet.column.number + i

        dataFormat = kwargs.get('dataFormat', None)
        if dataFormat:
            worksheet.cell.format = dataFormat        

        if value:
            kwargs['value'] = value * fraction
        
        set_cell(worksheet, **kwargs)

    return worksheet


def is_header(worksheet: Worksheet) -> bool:
    """
    Check if the current row is a header row.
    
    Args:
        worksheet: The worksheet to check.
        
    Returns:
        True if the current row is a header row, False otherwise.
    """
    return worksheet.row.number == worksheet.row.headerRow


def set_header_cell(worksheet: Worksheet, value: str, width: int, **kwargs) -> Worksheet:
    """
    Set properties for a header cell.
    
    Args:
        worksheet: The worksheet to modify.
        value: The text value to display in the header.
        width: The column width for the header.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    split = kwargs.pop('split', False)
    if not split:
        return set_cell(worksheet, value=value, width=width, fontName='Noto Mono', bold=True, **kwargs)
    
    for i, name in enumerate(worksheet.names):
        worksheet.column.number = worksheet.column.number + i
        set_header_cell(worksheet, value=f'{name} {value}', width=width + 2, **kwargs)
    
    return worksheet


#######################################################
# BOOKING IDENTIFIER/DETAILS CELLS
#######################################################

def set_id_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the booking ID cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='KLT ID', width=5, **kwargs)
 
    if booking:
        worksheet.cell.setToNumberFormat()
        return set_cell(worksheet, value=booking.id, **kwargs)
 
    return set_cell(worksheet, **kwargs)


def set_lead_guest_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the lead guest name cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Lead Guest', width=11, **kwargs)
    
    if booking:
        return set_cell(worksheet, value=booking.guest.prettyName, **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_booking_origin_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the booking origin/source cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Booking Origin', width=11, **kwargs)
    
    if booking:
        if booking.details.isOwner:
            value = 'OWNER'
        else:
            value = booking.details.enquirySource
        return set_cell(worksheet, value=value, **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_property_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the property name cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Property', width=10, **kwargs)
    
    if booking:
        return set_cell(worksheet, value=booking.property.shortName, **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_arrival_date_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the arrival date cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Arrival Date', width=10, **kwargs)
    
    if booking:
        if hasattr(worksheet, 'stringDates') and worksheet.stringDates:
            value = WorksheetDates.toStringDate(booking.arrival.date)
            return set_cell(worksheet, value=value, **kwargs)
            
        worksheet.cell.setToDateFormat()
        return set_cell(worksheet, value=booking.arrival.date, **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_departure_date_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the departure date cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Departure Date', width=10, **kwargs)
    
    if booking:
        if hasattr(worksheet, 'stringDates') and worksheet.stringDates:
            value = WorksheetDates.toStringDate(booking.departure.date)
            return set_cell(worksheet, value=value, **kwargs)
        worksheet.cell.setToDateFormat()
        return set_cell(worksheet, value=booking.departure.date, **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_total_guests_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the total number of guests cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Total Guests', width=7, **kwargs)
    
    if booking:
        worksheet.cell.setToNumberFormat()
        return set_cell(worksheet, value=booking.details.totalGuests, **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_total_nights_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the total number of nights cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Total Nights', width=7, **kwargs)
    
    if booking:
        worksheet.cell.setToNumberFormat()
        return set_cell(worksheet, value=booking.totalNights, **kwargs)
    
    return set_cell(worksheet, **kwargs)


#######################################################
# GUEST DETAILS CELLS
#######################################################

def set_passport_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the guest passport/ID card cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Passport/ID Card', width=14, **kwargs)
    
    if booking:
        return set_cell(worksheet, value=booking.guest.passport, **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_nif_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the guest NIF (Portuguese tax ID) cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Portuguese NIF', width=12, **kwargs)
    
    if booking:
        return set_cell(worksheet, value=booking.guest.nifNumber, **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_nationality_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the guest nationality cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Nationality', width=12, **kwargs)
    
    if booking:
        return set_cell(worksheet, value=booking.guest.nationality, **kwargs)
    
    return set_cell(worksheet, **kwargs)


#######################################################
# GUEST PAYMENT/CHARGES CELLS
#######################################################

def set_currency_used_by_guest_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the currency used by the guest cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Currency Used by Guest', width=12, **kwargs)
    
    if booking:
        worksheet.cell.setToTextFormat()
        return set_cell(worksheet, value=booking.charges.currency, **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_total_rental_received_by_klt_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the total rental amount received by KLT cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Total Rental Received by KLT Prop. Serv.', width=14, **kwargs)
    return set_basic_holiday_charge_cell(worksheet, booking, **kwargs)


def set_total_received_by_klt_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the total amount received by KLT cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Total Received by KLT Prop. Serv.', width=14, **kwargs)
    
    if booking:
        worksheet.cell.setToCurrencyFormat(booking.charges.currency)
        return set_cell(worksheet, value=booking.charges.totalRental, **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_basic_holiday_charge_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the basic holiday charge cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Basic Holiday Charge', width=10, **kwargs)
    
    if booking:
        worksheet.cell.setToCurrencyFormat(booking.charges.currency)
        return set_cell(worksheet, value=booking.charges.basicRental, **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_admin_charge_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the administrative charge cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Admin. Charge', width=10, **kwargs)
    
    if booking:
        worksheet.cell.setToCurrencyFormat(booking.charges.currency)
        return set_cell(worksheet, value=booking.charges.admin, **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_platform_fee_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the platform fee cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Platform Fee', width=10, **kwargs)
    
    if booking:
        worksheet.cell.setToCurrencyFormat(booking.charges.currency)
        return set_cell(worksheet, value=determine_platform_fee(booking), **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_platform_fee_iva_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the platform fee IVA (tax) cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Platform Fee IVA', width=10, **kwargs)
    
    if booking:
        worksheet.cell.setToCurrencyFormat(booking.charges.currency)
        return set_cell(worksheet, value=determine_platform_fee_IVA(booking), **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_platform_fee_plus_iva_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the platform fee plus IVA cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Platform Fee + IVA', width=10, **kwargs)
    
    if booking:
        worksheet.cell.setToCurrencyFormat(booking.charges.currency)
        return set_cell(worksheet, value=determine_platform_fee_with_IVA(booking), **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_total_to_be_receipted_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the total amount to be receipted cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Total to be Receipted', width=10, **kwargs)
    
    worksheet.cell.setToEurosFormat()
    if booking:
        value = determine_total_to_be_receipted(booking)
    else:
        value = 0
    return set_cell(worksheet, value=value, **kwargs)


#######################################################
# OWNER PAYMENT/CHARGES CELLS
#######################################################

def set_rental_to_owner_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the rental amount to be paid to owner cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Rental to Owner', width=10, **kwargs)
    
    if booking:
        worksheet.cell.setToCurrencyFormat(booking.charges.currency)
        if booking.charges.currency == 'GBP' and worksheet.internal:
            kwargs['color'] = '2986cc'
        return set_cell(worksheet, value=determine_owner_payment(booking), **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_management_fees_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the management fees (cleaning, etc.) cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Cleaning Fees, etc.', width=10, **kwargs)
    
    if booking:
        worksheet.cell.setToEurosFormat()
        return set_cell(worksheet, value=determine_management_fee(booking), **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_invoice_number_cell(worksheet: Worksheet, *args, **kwargs) -> Worksheet:
    """
    Set the invoice number cell.
    
    Args:
        worksheet: The worksheet to modify.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Invoice Nº', width=8, **kwargs)
    return set_cell(worksheet, **kwargs)


def set_invoice_total_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the invoice total amount cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Invoice Total', width=10, **kwargs)
    
    if booking:
        worksheet.cell.setToEurosFormat()
        return set_cell(worksheet, value=determine_owner_invoice(booking), **kwargs)
    
    return set_cell(worksheet, **kwargs)


#######################################################
# COMMISSIONS CELLS
#######################################################

def set_internal_commission_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the internal commission cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Internal Commission', width=12, **kwargs)
    
    if booking:
        worksheet.cell.setToCurrencyFormat(booking.charges.currency)
        return set_cell(worksheet, value=determine_commission(booking), **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_commission_after_iva_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the commission amount after IVA cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Comm. after IVA', width=10, **kwargs)
    
    if booking:
        worksheet.cell.setToCurrencyFormat(booking.charges.currency)
        return set_cell(worksheet, value=determine_commission_after_IVA(booking), **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_klt_commission_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set the KLT commission cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='KLT Commission', width=13, **kwargs)
    
    if booking:
        worksheet.cell.setToCurrencyFormat(booking.charges.currency)
        return set_cell(worksheet, value=determine_klt_commission(booking), **kwargs)
    
    return set_cell(worksheet, **kwargs)


def set_marias_commission_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set Maria's commission cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to get data from. If None, an empty cell will be created.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Maria\'s Commission', width=13, **kwargs)
    
    if booking:
        worksheet.cell.setToCurrencyFormat(booking.charges.currency)
        return set_cell(worksheet, value=determine_non_klt_commission(booking), **kwargs)
    
    return set_cell(worksheet, **kwargs)


#######################################################
# SHEET FUNCTIONS CELLS
#######################################################

def set_running_total_cell(worksheet: Worksheet, *args, **kwargs) -> Worksheet:
    """
    Set a running total cell (formula cell).
    
    Args:
        worksheet: The worksheet to modify.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='Running Total', width=10, **kwargs)
    worksheet.cell.setToEurosFormat()
    worksheet.cell.setRunningTotal()
    return set_cell(worksheet, **kwargs)


#######################################################
# CHECKED CELLS
#######################################################

def set_checked_cell(worksheet: Worksheet, applicable: bool = True, **kwargs) -> Worksheet:
    """
    Set a cell that represents a checked/not applicable status.
    
    Args:
        worksheet: The worksheet to modify.
        applicable: Whether the item is applicable. If True, shows a checkmark; if False, shows N/A.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if applicable:
        return set_cell(worksheet, fontSize=15, color='069a2e', bold=True, **kwargs)
    return set_cell(worksheet, value='N/A', fontSize=10, color='c02c38', **kwargs)


def set_paid_cell(worksheet: Worksheet, *args, **kwargs) -> Worksheet:
    """
    Set a payment status cell.
    
    Args:
        worksheet: The worksheet to modify.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='PAID?', width=8, **kwargs)
    return set_checked_cell(worksheet, **kwargs)


def set_invoiced_cell(worksheet: Worksheet, booking: Booking | None, **kwargs) -> Worksheet:
    """
    Set an invoice status cell.
    
    Args:
        worksheet: The worksheet to modify.
        booking: The booking to check invoice requirements for.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='INVOICED?', width=12, **kwargs)
   
    if booking:
        applicable = determine_need_for_invoice(booking)
    else:
        applicable = True
    return set_checked_cell(worksheet, applicable=applicable, **kwargs)


def set_issued_cell(worksheet: Worksheet, *args, **kwargs) -> Worksheet:
    """
    Set an issuance status cell.
    
    Args:
        worksheet: The worksheet to modify.
        **kwargs: Additional keyword arguments for cell properties.
        
    Returns:
        The modified worksheet.
    """
    if is_header(worksheet):
        return set_header_cell(worksheet, value='ISSUED?', width=10, **kwargs)
    return set_checked_cell(worksheet, **kwargs)