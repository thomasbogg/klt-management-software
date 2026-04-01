from default.booking.booking import Booking
from reports.internal.functions import (
    get_year_comparison_dict,
    split_by_location,
    set_month_rows,
    set_items,
    split_by_location,
    split_by_month,
    split_by_year,
)
from workbooks.utils import set_tables_in_worksheet
from workbooks.workbook import Workbook
from workbooks.worksheet import Worksheet


def extras_report_creator(workbook: Workbook, bookings: list[Booking]):
    """
    Create a report comparing bookings made versus enquiries.

    Args:
        workbook: The workbook to add the report to.
        bookings: A list of Booking objects.
    """
    worksheet: Worksheet = workbook.newSheet('Extras')
    locations = split_by_location(bookings=bookings, worksheet=worksheet)

    for i in range(len(locations)):
        location = locations[i]
        table = worksheet.tables[i]
        data = list()
        set_month_rows(table)

        extras = _split_for_extras(location, table=table)
        for i in range(len(extras)):
            extra = extras[i]
            column = table.columns[i]
            data += _calculate_totals(extra, column=column)

        table.data = data
    set_tables_in_worksheet(worksheet, adjustColumnWidths=False)


def _split_for_extras(bookings: list[Booking], **kwargs) -> dict:
    """
    Split bookings by month for extras.
    Args:
        bookings: A list of Booking objects.
    Returns:
        A list of lists, where each inner list contains bookings for a specific month.
    """
    # Set up a list for each month (1-12) plus a total at the end
    # Each inner list will hold bookings for that month
    # The last list will hold all bookings as a total
    result = [[] for _ in range(6)]
    set_items(
        [
            'Airport Transfers', 
            'Welcome Packs', 
            'Cots', 
            'High Chairs', 
            'Mid-stay Cleans', 
            'Late Check-outs'
        ], 
        **kwargs)
   
    for booking in bookings:
        if booking.extras.airportTransfers:
            result[0].append(booking)
            result[0].append(booking)
        elif booking.extras.airportTransferInboundOnly:
            result[0].append(booking)
        elif booking.extras.airportTransferOutboundOnly:
            result[0].append(booking)
        if booking.extras.welcomePack:
            result[1].append(booking)
        if booking.extras.cot:
            result[2].append(booking)
        if booking.extras.highChair:
            result[3].append(booking)
        if booking.extras.midStayClean:
            result[4].append(booking)
        if booking.extras.lateCheckout:
            result[5].append(booking)
    return result


def _calculate_totals(bookings: list[Booking], **kwargs) -> dict:
    """
    Calculate total management services for a list of bookings.

    Args:
        bookings: A list of Booking objects.

    Returns:
        A dictionary with total management services.
    """
    set_items(['Tot', 'Lst Yr'], **kwargs)
    totals = [[], []]
    byMonth = split_by_month(bookings)
    for bookings in byMonth:
        thisYear, lastYear = split_by_year(bookings)
        totals[0].append(len(thisYear))
        totals[1].append(get_year_comparison_dict(len(thisYear), len(lastYear)))
    return totals