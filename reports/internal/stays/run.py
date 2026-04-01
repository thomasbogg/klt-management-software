from default.booking.booking import Booking
from default.dates import dates
from reports.internal.functions import (
    calculate_totals,
    split_by_location,
    split_by_booking_source,
    split_by_owner_guest,
    set_month_rows,
    get_year_comparison_dict,
    get_percentage,
    set_items
)
from workbooks.utils import set_tables_in_worksheet
from workbooks.workbook import Workbook
from workbooks.worksheet import Worksheet


def stays_vs_nights_reports_creator(workbook: Workbook, bookings: list[Booking], onlyGuest: bool = False):

    """
    Create a report comparing stays and nights for bookings.

    Args:
        workbook: The workbook to add the report to.
        bookings: A list of Booking objects.
        onlyGuest: If True, only include guest bookings.
    """
    worksheet: Worksheet = workbook.newSheet('Guest Stays' if onlyGuest else 'All Stays')
    locations = split_by_location(bookings=bookings, worksheet=worksheet)
  
    for i in range(len(locations)):
        arrivalsComparator, nightsComparator = None, None
        location = locations[i]
        table = worksheet.tables[i]
        data = list()
        sourceFunc = split_by_booking_source if onlyGuest else split_by_owner_guest
        sources = sourceFunc(location, table=table)
        set_month_rows(table)
        
        for i in range(len(sources)):
            source = sources[i]
            column = table.columns[i]

            set_items(['Arrivals', 'Nights'], column=column)
            arrivalsColumn, nightsColumn = column.subcolumns

            arrivals = calculate_totals(source, arrivalsComparator, column=arrivalsColumn)
            nights = _calculate_nights_totals(source, nightsComparator, column=nightsColumn)

            if i == 0:  # First source, set comparators
                arrivalsComparator = arrivals[0] # index 0 is 'Tot' column data
                nightsComparator = nights[0] # index 0 is 'Tot' column data

            data += arrivals + nights
        table.data = data
    set_tables_in_worksheet(worksheet)


def _calculate_nights_totals(bookings: list[Booking], comparator=None, **kwargs) -> dict:
    set_items(['Tot', '%', 'Lst Yr'], **kwargs)
    thisYear, lastYear = [0 for _ in range(13)], [0 for _ in range(13)]

    for booking in bookings:
        yearsMonthsDays = dates.daysperMonth(booking.arrival.date, booking.departure.date)

        for year, months in yearsMonthsDays.items():
            current = None

            if year == dates.year():
                current = thisYear 
            elif year == dates.year(-1):
                current = lastYear
            
            if current:
                for month, days in months.items():
                    current[month - 1] += days
                    current[12] += days

    result = [thisYear, [], []]
    for i in range(13):
        result[1].append(get_percentage(thisYear[i], comparator[i] if comparator else None))
        result[2].append(get_year_comparison_dict(thisYear[i], lastYear[i]))
    return result