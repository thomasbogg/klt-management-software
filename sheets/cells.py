from default.booking.booking import Booking
from default.booking.functions import determine_management_fee, determine_meet_greet, determine_clean
from default.property.property import Property
from default.workbook.cells import set_cell
from default.booking.functions import determine_owner_payment as default_determine_owner_payment
from workbooks.worksheet import Worksheet


def set_id_cell(worksheet: Worksheet, booking: Booking=None, **kwargs):
    if worksheet.row.count == 7:
        cell = worksheet.cell
        cell.rows = 2
        cell.merge()
        return set_cell(worksheet, value='ID', width=6, **single_header_kwargs())
    
    if booking:
        return set_cell(worksheet, value=booking.id, **data_kwargs(horizontal='right', **kwargs))
    return set_cell(worksheet, **data_kwargs(horizontal='right', **kwargs))


def set_date_cell(worksheet: Worksheet, booking: Booking=None, **kwargs):
    if worksheet.row.count == 8:
        return set_cell(worksheet, value='Date', width=10, **lower_header_kwargs())
    
    worksheet.cell.setToDateFormat()
 
    if (kwargs.get('value', False) or booking) and kwargs.get('isDeparture', False):
        color = 'FFFF0000'
    else:
        color = '00000000'

    if booking:
        value = booking.departure.date if kwargs.get('isDeparture', False) else booking.arrival.date
        return set_cell(worksheet, value=value, **data_kwargs(horizontal='right', color=color, **kwargs))
    
    return set_cell(worksheet, **data_kwargs(horizontal='right', color=color, **kwargs))


def set_time_cell(worksheet: Worksheet, booking: Booking=None, **kwargs):
    if worksheet.row.count == 8:
        return set_cell(worksheet, value='Time', width=7, **lower_header_kwargs())
    
    worksheet.cell.setToTimeFormat()

    if booking:
        isDeparture = kwargs.get('isDeparture', False)
        return set_cell(worksheet, value=determine_time(booking, isDeparture), **data_kwargs(horizontal='right', **kwargs))
   
    return set_cell(worksheet, **data_kwargs(horizontal='right', **kwargs))


def set_details_cell(worksheet: Worksheet, booking: Booking=None, **kwargs):
    if worksheet.row.count == 8:
        return set_cell(worksheet, value='Details', width=17, **lower_header_kwargs())

    if booking:
        isDeparture = kwargs.get('isDeparture', False)
        return set_cell(worksheet, value=determine_details(booking, isDeparture), **data_kwargs(**kwargs))
  
    return set_cell(worksheet, **data_kwargs(**kwargs))


def set_lead_guest_cell(worksheet: Worksheet, booking: Booking=None, **kwargs):
    if worksheet.row.count == 8:
        return set_cell(worksheet, value='Name', width=18, **lower_header_kwargs())

    if booking:
        if booking.details.enquirySource == 'Direct':
            if not booking.property.owner.isPaidRegularly:
                return set_cell(worksheet, value=booking.guest.prettyName, **data_kwargs(color='00008000'))
        return set_cell(worksheet, value=booking.guest.prettyName, **data_kwargs(**kwargs))
    return set_cell(worksheet, **data_kwargs(**kwargs))


def set_group_cell(worksheet: Worksheet, booking: Booking=None, **kwargs):
    if worksheet.row.count == 8:
        return set_cell(worksheet, value='Group', width=9, **lower_header_kwargs())

    if booking:
        return set_cell(worksheet, value=booking.details.prettyGuests, **data_kwargs(**kwargs))
    return set_cell(worksheet, **data_kwargs(**kwargs))


def set_contact_cell(worksheet: Worksheet, booking: Booking=None, **kwargs):
    if worksheet.row.count == 8:
        return set_cell(worksheet, value='Contact', width=25, **lower_header_kwargs())

    if booking:
        isDeparture = kwargs.get('isDeparture', False)
        if isDeparture:
            return set_cell(worksheet, value=booking.guest.email, **data_kwargs(**kwargs))
        return set_cell(worksheet, value=booking.guest.phone, **data_kwargs(**kwargs))
   
    return set_cell(worksheet, **data_kwargs(**kwargs))


def set_extras_cell(worksheet: Worksheet, booking: Booking=None, **kwargs):
    cell = worksheet.cell
    cell.columns = 3
    if worksheet.row.count == 7:
        cell.rows = 2
        cell.merge()
        return set_cell(worksheet, value='Extras', width=14, **single_header_kwargs())
    
    cell.merge()
  
    if booking:
        isDeparture = kwargs.get('isDeparture', False)
        if isDeparture:
            value = booking.extras.prettyDeparture
        else:
            value = booking.extras.prettyArrival
    
    set_cell(worksheet, **data_kwargs(**kwargs))
    worksheet.column.number = 10
    return worksheet


def set_meet_greet_cell(worksheet: Worksheet, booking: Booking=None, **kwargs):
    if worksheet.row.count == 8:
        return set_cell(worksheet, value='M & G', width=8, **lower_header_kwargs())

    if booking and booking.details.isOwner:
        return set_cell(worksheet, value=int(determine_meet_greet(booking)), **data_kwargs(horizontal='right', **kwargs))
    return set_cell(worksheet, **data_kwargs(horizontal='right', **kwargs))


def set_clean_cell(worksheet: Worksheet, booking: Booking=None, **kwargs):
    if worksheet.row.count == 8:
        return set_cell(worksheet, value='Clean', width=8, **lower_header_kwargs())
    
    worksheet.cell.setToNumberFormat()

    if booking and booking.details.isOwner:
        return set_cell(worksheet, value=int(determine_clean(booking)), **data_kwargs(horizontal='right', **kwargs))
    return set_cell(worksheet, **data_kwargs(horizontal='right', **kwargs))


def set_basic_cell(worksheet: Worksheet, booking: Booking=None, **kwargs):
    if worksheet.row.count == 8:
        return set_cell(worksheet, value='Basic', width=9, **lower_header_kwargs())
    
    worksheet.cell.setToEurosFormat()

    if booking and booking.property.weClean:
        isDeparture = kwargs.get('isDeparture', False)
        if isDeparture:
            return set_cell(worksheet, value=determine_management_fee(booking), **data_kwargs(horizontal='right', **kwargs))
    return set_cell(worksheet, **data_kwargs(horizontal='right', **kwargs))


def set_additional_cell(worksheet: Worksheet, booking: Booking=None, **kwargs):
    if worksheet.row.count == 8:
        return set_cell(worksheet, value='Additional', width=12, **lower_header_kwargs())
    
    worksheet.cell.setToEurosFormat()
    
    if booking:
        isDeparture = kwargs.get('isDeparture', False)
        if not isDeparture:
            value = determine_owner_payment(booking)
            if value:
                return set_cell(worksheet, value=value, **data_kwargs(horizontal='right', **kwargs))
    return set_cell(worksheet, **data_kwargs(horizontal='right', **kwargs))
    

def set_cost_cell(worksheet: Worksheet, *args, **kwargs):
    if worksheet.row.count == 8:
        return set_cell(worksheet, value='Cost', width=10, **lower_header_kwargs())

    cell = worksheet.cell
    cell.setToEurosFormat()
    cell.setTotal()
    return set_cell(worksheet, **data_kwargs(horizontal='right', **kwargs))


def set_run_tot_cell(worksheet: Worksheet, *args, **kwargs):
    if worksheet.row.count == 8:
        return set_cell(worksheet, width=10, value='Run. Tot.', **lower_header_kwargs())
    
    cell = worksheet.cell
    cell.setToEurosFormat()
    cell.setRunningTotal()
    return set_cell(worksheet, **data_kwargs(horizontal='right', **kwargs))


def set_observations_cell(worksheet: Worksheet, *args, **kwargs):
    if worksheet.row.count == 8:
        return set_cell(worksheet, value='Observations', width=25, **lower_header_kwargs())
    return set_cell(worksheet, **data_kwargs(**kwargs))
    

def set_arrival_departure_cell(worksheet: Worksheet):
    cell = worksheet.cell
    cell.columns = 3
    cell.merge()
    return set_cell(worksheet, value='Arrival and Departure', **upper_header_kwargs())


def set_guest_details_cell(worksheet: Worksheet):
    cell = worksheet.cell
    cell.columns = 3
    cell.merge()
    return set_cell(worksheet, value='Guest Details', **upper_header_kwargs())


def set_owner_details_cell(worksheet: Worksheet):
    cell = worksheet.cell
    cell.columns = 2
    cell.merge()
    return set_cell(worksheet, value='Owner Details', **upper_header_kwargs())


def set_charges_observations_cell(worksheet: Worksheet):
    cell = worksheet.cell
    cell.columns = 5
    cell.merge()
    return set_cell(worksheet, value='Charges and Observations', **upper_header_kwargs())


def set_property_header(worksheet: Worksheet, property: Property):
    set_title_cell(worksheet, property.name)
    row = worksheet.row
  
    row.number = 3
    row.height = 20
    set_owner_detail_cell(worksheet, property.owner.name)
    set_property_labels_cell(worksheet, 'NIF:')
    set_property_details_cell(worksheet, property.owner.nifNumber)
  
    row.number = 4
    row.height = 20
    set_owner_detail_cell(worksheet, property.owner.phone)
    set_property_labels_cell(worksheet, 'KeyBox:')
    set_property_details_cell(worksheet, '')
  
    row.number = 5
    row.height = 20
    set_owner_detail_cell(worksheet, property.owner.email)
    set_property_labels_cell(worksheet, 'WiFi:')
    set_property_details_cell(worksheet, '')

    row.number = 6
    row.height = 20
    set_owner_detail_cell(worksheet)
    set_property_labels_cell(worksheet)
    set_property_details_cell(worksheet)
    return worksheet


def set_column_headers(worksheet: Worksheet):
    row = worksheet.row
    column = worksheet.column

    row.number = 7
    row.height = 25
    column.number = 1
    set_id_cell(worksheet)
    column.number = 2
    set_arrival_departure_cell(worksheet)
    column.number = 5
    set_guest_details_cell(worksheet)
    column.number = 8
    set_extras_cell(worksheet)
    column.number = 11
    set_owner_details_cell(worksheet)
    column.number = 13
    set_charges_observations_cell(worksheet)

    row.number = 8
    row.height = 20
    column.number = 2
    set_date_cell(worksheet)
    column.number = 3
    set_time_cell(worksheet)
    column.number = 4
    set_details_cell(worksheet)
    column.number = 5
    set_lead_guest_cell(worksheet)
    column.number = 6
    set_group_cell(worksheet)
    column.number = 7
    set_contact_cell(worksheet)
    column.number = 11
    set_meet_greet_cell(worksheet)
    column.number = 12
    set_clean_cell(worksheet)
    column.number = 13
    set_basic_cell(worksheet)
    column.number = 14
    set_additional_cell(worksheet)
    column.number = 15
    set_cost_cell(worksheet)
    column.number = 16
    set_run_tot_cell(worksheet)
    column.number = 17
    set_observations_cell(worksheet)
  
    return worksheet


def set_title_cell(worksheet: Worksheet, propertyName: str):
    worksheet.row.count = 1
    worksheet.column.count = 7  
    cell = worksheet.cell
    cell.columns = 6
    cell.rows = 2
    cell.merge()
    return set_cell(worksheet, value=propertyName, **property_title_kwargs())


def set_owner_detail_cell(worksheet: Worksheet, value: str=None):
    worksheet.column.number = 7
    cell = worksheet.cell
    cell.columns = 2
    cell.merge()
    return set_cell(worksheet, value=value, **owner_details_kwargs())
		

def set_property_labels_cell(worksheet: Worksheet, value: str=None):
    worksheet.column.number = 9
    return set_cell(worksheet, value=value, width=12, **property_label_kwargs())


def set_property_details_cell(worksheet: Worksheet, value: str=None):
    worksheet.column.number = 10
    cell = worksheet.cell
    cell.columns = 3
    cell.merge()
    return set_cell(worksheet, value=value, **property_detail_kwargs())


def data_kwargs(**kwargs):
    style = {
        'fontSize': 10,
        'fontName': 'Free Sans',
        'horizontal': 'left',
    }
    style.update(kwargs)
    return style


def property_title_kwargs():
    return {
        'fontSize': 20,
        'fontName': 'Courier New',
        'bold': True,
        'horizontal': 'center',
    }


def owner_details_kwargs():
    return {
        'fontSize': 11,
        'horizontal': 'left',
        'fontName': 'Courier New',
        'bold': False,
    }


def property_detail_kwargs():
    style = owner_details_kwargs()
    style.update({
        'horizontal': 'right',
    })
    return style


def property_label_kwargs():
    return {
        'fontSize': 12,
        'horizontal': 'left',
        'fontName': 'Courier New',
        'bold': False,
    }


def single_header_kwargs():
    return {
        'fontSize': 12,
        'fontName': 'Roboto',
        'bold': True,
        'borderLeft': 'thin',
    }


def upper_header_kwargs():
    style = single_header_kwargs()
    style.update({
        'borderBottom': 'thin',
        'bold': False,
    })
    return style


def lower_header_kwargs():
    style = single_header_kwargs()
    style.update({
        'fontSize': 11,
        'fontName': 'Arial',
    })
    return style


def determine_owner_payment(booking):
    if not booking.property.weBook:
        return None
    if booking.property.owner.isPaidRegularly:
        return None
    return - default_determine_owner_payment(booking)



def determine_time(booking: Booking, isDeparture: bool=False) -> str:
    if isDeparture:
        if booking.departure.timeIsValid:
            return booking.departure.time
    else:
        if booking.arrival.timeIsValid:
            return booking.arrival.time
    return ''


def determine_details(booking: Booking, isDeparture: bool=False) -> str:
    if isDeparture:
        booking = booking.departure
    else:
        booking = booking.arrival
    
    details = []
    if booking.flightNumber:
        details.append(booking.flightNumber)
      
        if not booking.isFaro:
            details.append('(LISBON)')
      
        if booking.details:
            details.append(f'- {booking.details}')
        return ' '.join(details)
    
    details = booking.prettyDetails
    if 'Unk.' in details:
        return ''
    return details
    
