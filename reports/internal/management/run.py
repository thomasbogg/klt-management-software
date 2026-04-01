from default.booking.booking import Booking
from default.booking.functions import (
    determine_clean,
    determine_meet_greet,
)
from reports.internal.functions import (
    calculate_totals,
    split_by_location,
    set_month_rows,
    set_items,
)
from workbooks.utils import set_tables_in_worksheet
from workbooks.workbook import Workbook
from workbooks.worksheet import Worksheet


def management_report_creator(workbook: Workbook, bookings: list[Booking]):
    """
    Create a report comparing bookings made versus enquiries.

    Args:
        workbook: The workbook to add the report to.
        bookings: A list of Booking objects.
    """
    worksheet: Worksheet = workbook.newSheet('Management')
    sources = _split_by_source(bookings=bookings, worksheet=worksheet)

    for i in range(len(sources)):
        cleansComparator, meetGreetComparator = None, None
        source = sources[i]
        table = worksheet.tables[i]
        data = list()
        locations = split_by_location(source, table=table)
        set_month_rows(table)
        
        for i in range(len(locations)):
            location = locations[i]
            column = table.columns[i]

            set_items(['Cleans', 'Meet & Greets'], column=column)
            cleansColumn, meetGreetColumn = column.subcolumns

            cleans = calculate_totals(
                                    location, 
                                    cleansComparator, 
                                    calcFunc=determine_clean, 
                                    column=cleansColumn, 
                                    dateAttrs=['departure'])
            meetGreet = calculate_totals(
                                    location, 
                                    meetGreetComparator, 
                                    calcFunc=determine_meet_greet, 
                                    column=meetGreetColumn)

            if i == 0:  # First source, set comparators
                cleansComparator = cleans[0] # index 0 is 'Tot' column data
                meetGreetComparator = meetGreet[0] # index 0 is 'Tot' column data

            data += cleans + meetGreet
        table.data = data
    set_tables_in_worksheet(worksheet)


def _split_by_source(bookings: list[Booking], **kwargs) -> dict:
    """
    Split bookings by source and calculate totals.

    Args:
        bookings: A list of Booking objects.
        kwargs: Additional keyword arguments.

    Returns:
        A dictionary with totals for each source.
    """
    set_items(['ALL', 'Algarve Beach Apartments', 'KKLJ'], **kwargs)
    result = [bookings, [], []]
    for booking in bookings:
        if booking.details.enquirySource == 'KKLJ':
            result[2].append(booking)
        else:
            result[1].append(booking)
    return result