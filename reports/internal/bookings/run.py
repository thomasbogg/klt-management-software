from default.booking.booking import Booking
from reports.internal.functions import (
    calculate_totals,
    split_by_location,
    split_by_booking_source,
    set_month_rows,
    set_items,
)
from workbooks.utils import set_tables_in_worksheet
from workbooks.workbook import Workbook
from workbooks.worksheet import Worksheet


def bookings_vs_enquiries_report_creator(workbook: Workbook, bookings: list[Booking]):

    """
    Create a report comparing bookings made versus enquiries.

    Args:
        workbook: The workbook to add the report to.
        bookings: A list of Booking objects.
    """
    worksheet: Worksheet = workbook.newSheet('Bookings')
    locations = split_by_location(bookings=bookings, worksheet=worksheet)

    for i in range(len(locations)):
        bookingsComparator, enquiriesComparator = None, None
        location = locations[i]
        table = worksheet.tables[i]
        data = list()
        sources = split_by_booking_source(location, table=table)
        set_month_rows(table)
        
        for i in range(len(sources)):
            source = sources[i]
            column = table.columns[i]

            set_items(['Bookings', 'Enquiries'], column=column)
            bookingsColumn, enquiriesColumn = column.subcolumns

            okay, notOkay = _sort_bookings_enquiries(source)
            bookings = calculate_totals(okay, bookingsComparator, column=bookingsColumn, dateAttrs=['details', 'enquiryDate'])
            enquiries = calculate_totals(notOkay, enquiriesComparator, column=enquiriesColumn, dateAttrs=['details', 'enquiryDate'])

            if i == 0:  # First source, set comparators
                bookingsComparator = bookings[0] # index 0 is 'Tot' column data
                enquiriesComparator = enquiries[0] # index 0 is 'Tot' column data

            data += bookings + enquiries
        table.data = data
    set_tables_in_worksheet(worksheet)


def _sort_bookings_enquiries(bookings: list[Booking]) -> dict:

    def __append(booking: Booking, bookedAnyway):
        if booking.arrival.year not in bookedAnyway:
            bookedAnyway[booking.arrival.year] = {}
        if booking.arrival.month not in bookedAnyway[booking.arrival.year]:
            bookedAnyway[booking.arrival.year][booking.arrival.month] = []
        bookedAnyway[booking.arrival.year][booking.arrival.month].append(booking.guest.id)

    okay, notOkay = [], []
    bookedAnyway = {}
    for booking in bookings:
        if booking.details.statusIsOkay:
            okay.append(booking)
            __append(booking, bookedAnyway)

    for booking in bookings:
        if booking.details.statusIsOkay:
            continue
        if booking.guest.id in bookedAnyway.get(booking.arrival.year, {}).get(booking.arrival.month, []):
            continue
        notOkay.append(booking)
        __append(booking, bookedAnyway)

    return okay, notOkay