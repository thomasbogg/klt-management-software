from default.booking.booking import Booking
from default.booking.functions import (
    determine_clean,
    determine_meet_greet,
    determine_total_paid_by_guest,
    determine_total_paid_to_klt,
    determine_commission,
    determine_klt_commission,
    determine_owner_payment,
    )
from default.database.functions import search_properties
from reports.internal.functions import (
    get_percentage,
    set_items,
    currency_value_formatter,
)
from workbooks.utils import set_tables_in_worksheet
from workbooks.workbook import Workbook
from workbooks.worksheet import Worksheet
from workbooks.tables import Table


def properties_report_creator(workbook: Workbook, bookings: list[Booking]) -> None:
    """
    Create a report for properties based on bookings.

    Args:
        workbook: The workbook to add the report to.
        bookings: A list of Booking objects.
    """
    worksheet: Worksheet = workbook.newSheet('Properties')
    table = worksheet.table()
    for i in range(len(columns())):
        width = 8 if i < 16 else 15
        table.column(name=columns()[i], width=width)

    properties = get_properties()
    split = _split_for_properties(bookings, properties, table=table)

    data = [[] for _ in range(len(columns()))]
    for bookings in split:
        data[0] += [len([booking for booking in bookings if booking.details.isOwner])]
        data[1] += [sum([booking.totalNights for booking in bookings if booking.details.isOwner])]
        data[2] += [get_percentage(data[1][-1], 365) ]
        data[3] += [len([booking for booking in bookings if not booking.details.isOwner])]
        data[4] += [sum([booking.totalNights for booking in bookings if not booking.details.isOwner])]
        data[5] += [get_percentage(data[4][-1], 365)]
        data[6] += [len([booking for booking in bookings if booking.details.enquirySource == 'Direct'])]
        data[7] += [sum([booking.totalNights for booking in bookings if booking.details.enquirySource == 'Direct'])]
        data[8] += [len([booking for booking in bookings if booking.details.enquirySource == 'Booking.com'])]
        data[9] += [sum([booking.totalNights for booking in bookings if booking.details.enquirySource == 'Booking.com'])]
        data[10] += [len([booking for booking in bookings if booking.details.enquirySource == 'Airbnb'])]
        data[11] += [sum([booking.totalNights for booking in bookings if booking.details.enquirySource == 'Airbnb'])]
        data[12] += [len([booking for booking in bookings if booking.details.enquirySource == 'Vrbo'])]
        data[13] += [sum([booking.totalNights for booking in bookings if booking.details.enquirySource == 'Vrbo'])]
        data[14] += [sum((int(determine_clean(booking)) for booking in bookings))]
        data[15] += [sum(int(determine_meet_greet(booking)) for booking in bookings)]
        data[16] += [sum(determine_total_paid_by_guest(booking) for booking in bookings)]
        data[17] += [sum(determine_total_paid_to_klt(booking) for booking in bookings)]
        data[18] += [sum(determine_owner_payment(booking) for booking in bookings)]
        data[19] += [sum(determine_commission(booking) for booking in bookings)]
        data[20] += [sum(determine_klt_commission(booking) for booking in bookings)]
        data[21] += [sum(determine_estimated_net_worth(booking) for booking in bookings)]

    for i in range(16, 22):
        data[i] = currency_value_formatter(data[i])

    table.data = data
    set_tables_in_worksheet(worksheet, adjustColumnWidths=False)


def _split_for_properties(bookings: list[Booking], properties: list[str], table: Table, **kwargs):
    """
    Split bookings by properties.
    Args:
        bookings: A list of Booking objects.
        properties: A list of property names.
    Returns:
        A list of lists, where each inner list contains bookings for a specific property.
    """
    result = [[] for _ in range(len(properties))]

    for property in properties:
        table.row(name=property)

    for booking in bookings:
        if booking.property.shortName not in properties:
            continue
        index = properties.index(booking.property.shortName)
        result[index].append(booking)

    return result


def columns():
    return [
        'Owner Bookings',
        'Owner Nights',
        'Owner Occupancy',
        'Guest Bookings',
        'Guest Nights',
        'Guest Occupancy',
        'Direct Bookings',
        'Direct Nights',
        'Booking.com Bookings',
        'Booking.com Nights',
        'Airbnb Bookings',
        'Airbnb Nights',
        'Vrbo Bookings',
        'Vrbo Nights',
        'Cleans',
        'Meet & Greets',
        'Yr Guest Payments',
        'Yr Revenue',
        'Yr Payouts',
        'Yr Commission',
        'Yr KLT Net Comm',
        'Est Net Worth to KLT',
    ]


def get_properties() -> list[str]:
    """
    Get a list of properties.

    Returns:
        A list of property names.
    """
    database = search_properties()
    search = database

    select = search.properties.select()
    select.weClean()
    select.weBook()
    select.addressId()

    properties = search.fetchall()
    database.close()

    locations = {}

    for property in properties:
        if not property.weBook and not property.weClean:
            continue
        if property.addressId not in locations:
            locations[property.addressId] = []
        locations[property.addressId].append(property.shortName)
   
    result = []
    for names in locations.values():
        names = sorted(names)
        for name in names:
            result.append(name)
    return result


def determine_estimated_net_worth(booking: Booking) -> float:
    """
    Determine the estimated net worth of a booking.

    Args:
        booking: A Booking object.

    Returns:
        The estimated net worth of the booking.
    """
    total = 0.0
    if not booking.details.isOwner:
        total += determine_klt_commission(booking)
    if booking.arrival.meetGreet:
        total += 4
    if booking.departure.clean:
        total += 10
    return total