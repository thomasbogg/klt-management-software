from default.booking.booking import Booking
from default.booking.functions import (
    determine_total_paid_by_guest,
    determine_klt_received_payment,
)
from reports.internal.functions import (
    euro_value_formatter,
    calculate_totals,
    split_by_location,
    split_by_booking_source,
    set_month_rows,
    set_items,
)
from workbooks.utils import set_tables_in_worksheet
from workbooks.workbook import Workbook
from workbooks.worksheet import Worksheet


def revenue_report_creator(workbook: Workbook, bookings: list[Booking]):
    """
    Create a report comparing bookings made versus enquiries.

    Args:
        workbook: The workbook to add the report to.
        bookings: A list of Booking objects.
    """
    worksheet: Worksheet = workbook.newSheet('Revenue')
    locations = split_by_location(bookings=bookings, worksheet=worksheet)

    for i in range(len(locations)):
        paidByGuestComparator, receivedByKLTComparator = None, None
        location = locations[i]
        table = worksheet.tables[i]
        data = list()
        sources = split_by_booking_source(location, table=table)
        set_month_rows(table)
        
        for i in range(len(sources)):
            source = sources[i]
            column = table.columns[i]

            set_items(['Paid by Guest', 'Rcvd by KLT'], column=column)
            paidByGuestColumn, receivedByKLTColumn = column.subcolumns

            paidByGuest = calculate_totals(source, paidByGuestComparator, calcFunc=determine_total_paid_by_guest, column=paidByGuestColumn)
            receivedByKLT = calculate_totals(source, receivedByKLTComparator, calcFunc=determine_klt_received_payment, column=receivedByKLTColumn)

            if i == 0:  # First source, set comparators
                paidByGuestComparator = paidByGuest[0] # index 0 is 'Tot' column data
                receivedByKLTComparator = receivedByKLT[0] # index 0 is 'Tot' column data

            data += paidByGuest + receivedByKLT
        table.data = [euro_value_formatter(lst) for lst in data]
    set_tables_in_worksheet(worksheet)