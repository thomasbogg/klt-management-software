from default.booking.booking import Booking
from default.booking.functions import (
    determine_owner_payment,
)
from reports.internal.functions import (
    euro_value_formatter,
    pound_value_formatter,
    calculate_totals,
    set_month_rows,
    set_items,
)
from libraries.workbook.utils import set_tables_in_worksheet
from libraries.workbook.workbook import Workbook
from libraries.workbook.worksheet import Worksheet


def accounts_report_creator(workbook: Workbook, bookings: list[Booking]):
    """
    Create a report comparing bookings made versus enquiries.

    Args:
        workbook: The workbook to add the report to.
        bookings: A list of Booking objects.
    """
    worksheet: Worksheet = workbook.newSheet('Accounts')

    fromKLTcomparator, fromWiseComparator = None, None
    table = worksheet.table(name='Payouts to Owners')
    data = list()
    set_month_rows(table)

    currencies = _split_by_euros_pounds(bookings, table=table)

    for i in range(len(currencies)):
        currency = currencies[i]
        column = table.columns[i]

        set_items(['From KLT', 'From WISE'], column=column)
        fromKLTColumn, fromWiseColumn = column.subcolumns

        kltBookings, wiseBookings = _sort_bookings_by_visibility(currency)

        fromKLT = calculate_totals(kltBookings, fromKLTcomparator, calcFunc=determine_owner_payment, column=fromKLTColumn)
        fromWISE = calculate_totals(wiseBookings, fromWiseComparator, calcFunc=determine_owner_payment, column=fromWiseColumn)

        if i == 0:  # First source, set comparators
            fromKLTcomparator = fromKLT[0] # index 0 is 'Tot' column data
            fromWiseComparator = fromWISE[0] # index 0 is 'Tot' column data

        fromKLT = [euro_value_formatter(lst) for lst in fromKLT]
        fromWISE = [pound_value_formatter(lst) if i == 2 else euro_value_formatter(lst) for lst in fromWISE]
        data += fromKLT + fromWISE
 
    table.data = data
    set_tables_in_worksheet(worksheet)


def _sort_bookings_by_visibility(bookings: list[Booking]) -> dict:
    """
    Sort bookings into visible and not visible based on their management status.
    
    Args:
        bookings: A list of Booking objects.
    
    Returns:
        A tuple containing two lists: visible bookings and not visible bookings.
    """
    full = []
    partial = []
    for booking in bookings:
        if booking.details.enquirySource != 'Direct':
            full.append(booking)
        else:
            partial.append(booking)
    return full, partial


def _split_by_euros_pounds(bookings: list[Booking], **kwargs) -> dict:
    """
    Split bookings by euros and pounds based on the provided calculation function.
    
    Args:
        bookings: A list of Booking objects.
        calcFunc: A callable function to calculate the value.
    
    Returns:
        A dictionary with two keys: 'euros' and 'pounds', each containing a list of calculated values.
    """
    set_items(['All', 'Euros', 'Pounds'], **kwargs)
    result = [bookings, [], []]
    for booking in bookings:
        booking.charges.applyExchangeRate = False
        if booking.charges.currency != 'EUR':
            if booking.property.owner.takesBothCurrencies:
                result[2].append(booking)
                booking.charges.applyExchangeRate = True
                continue

        result[1].append(booking)
    return result