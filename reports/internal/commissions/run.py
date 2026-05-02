from dates import dates
from default.booking.booking import Booking
from default.booking.functions import (
    determine_klt_commission,
    determine_non_klt_commission,
)
from reports.internal.functions import (
    euro_value_formatter,
    get_year_comparison_dict,
    set_items,
    set_month_rows,
    split_by_booking_source,
    split_by_location,
    split_by_month,
)
from workbooks.utils import set_tables_in_worksheet
from workbooks.workbook import Workbook
from workbooks.worksheet import Worksheet


def commissions_report_creator(workbook: Workbook, bookings: list[Booking]):
    """
    Create a report comparing bookings made versus enquiries.

    Args:
        workbook: The workbook to add the report to.
        bookings: A list of Booking objects.
    """
    worksheet: Worksheet = workbook.newSheet('Commissions')
    locations = split_by_location(bookings=bookings, worksheet=worksheet)

    for i in range(len(locations)):
        location = locations[i]
        table = worksheet.tables[i]
        data = list()
        sources = split_by_booking_source(location, table=table)
        set_month_rows(table)
        
        for i in range(len(sources)):
            source = sources[i]
            column = table.columns[i]

            set_items(['KLT', 'Maria'], column=column)
            for column in column.subcolumns:
                set_items(['Pre-IVA', 'Post-IVA', 'Lst Yr'], column=column)

            data += _calculate_commissions_totals(source)
        table.data = [euro_value_formatter(lst) for lst in data]
    set_tables_in_worksheet(worksheet)


def _calculate_commissions_totals(bookings: list[Booking], **kwargs) -> dict:
    """
    Calculate total commissions for a list of bookings.

    Args:
        bookings: A list of Booking objects.
        comparator: A dictionary with totals to compare against.

    Returns:
        A dictionary with total commissions.
    """
    def __calculate_month(bookings: list[Booking], ) -> dict:
        """
        Calculate the commission for a booking.
        """
        monthTotals = [0, 0, 0, 0, 0, 0]  # Pre-IVA KLT, Post-IVA KLT, Lst Yr KLT, Pre-IVA Maria, Post-IVA Maria, Last Year Maria
        for booking in bookings:
            postIVAKLT = determine_klt_commission(booking, postIVA=True)
            postIVAMaria = determine_non_klt_commission(booking, postIVA=True)
           
            if booking.arrival.year == dates.year():
                preIVAKLT = determine_klt_commission(booking, postIVA=False)
                preIVAMaria = determine_non_klt_commission(booking, postIVA=False)
                monthTotals[0] += preIVAKLT
                monthTotals[1] += postIVAKLT
                monthTotals[3] += preIVAMaria
                monthTotals[4] += postIVAMaria
            elif booking.arrival.year == dates.year(-1):
                monthTotals[2] += postIVAKLT
                monthTotals[5] += postIVAMaria
        return monthTotals

    result = [[], [], [], [], [], []]
    byMonth: list[list] = split_by_month(bookings, **kwargs)
    for bookings in byMonth:
        month = __calculate_month(bookings)
        result[0].append(month[0])
        result[1].append(month[1])
        result[2].append(get_year_comparison_dict(month[0], month[2]))
        result[3].append(month[3])
        result[4].append(month[4])
        result[5].append(get_year_comparison_dict(month[3], month[5]))
    return result