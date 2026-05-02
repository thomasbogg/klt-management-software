import datetime

from default.booking.functions import logbooking
from workbooks.tables import Table
from workbooks.worksheet import Worksheet
from default.dates import dates
from default.booking.booking import Booking
from workbooks.stylesheet import Stylesheet


def generic_calculator_function(*args, **kwargs):
    """
    A generic calculator function that returns a fixed value.
    """
    return 1


def calculate_totals(
    bookings: list[Booking], 
    comparator=None, 
    calcFunc: callable = generic_calculator_function, 
    **kwargs) -> dict:
    """
    Calculate total gross and nights for a list of bookings.

    Args:
        bookings: A list of Booking objects.
        comparator: A dictionary with totals to compare against.
        attribute: A tuple of attribute names to retrieve or a callable function.

    Returns:
        A dictionary with total gross and nights.
    """
    set_items(['Tot', '%', 'Lst Yr'], **kwargs)
    totals: list[list] = [[], [], []]
    byMonth: list[list] = split_by_month(bookings, **kwargs)
    for bookings in byMonth:
        thisYear, lastYear = get_year_totals(bookings, calcFunc=calcFunc, **kwargs)
        totals[0].append(thisYear)
        totals[1].append(get_percentage(
            thisYear, comparator[byMonth.index(bookings)] if comparator else None
        ))
        totals[2].append(get_year_comparison_dict(thisYear, lastYear))
    return totals


def euro_value_formatter(values: list[float | int | str | dict]) -> str:
    """
    Format a list of values as Euro currency.

    Args:
        values: A list of float, int, or str values to format.

    Returns:
        A string with the formatted Euro values.
    """
    return currency_value_formatter(values, currency='€')


def pound_value_formatter(values: list[float | int | str | dict]) -> str:
    """
    Format a list of values as Pound currency.

    Args:
        values: A list of float, int, or str values to format.

    Returns:
        A string with the formatted Pound values.
    """
    return currency_value_formatter(values, currency='£')


def currency_value_formatter(
    values: list[float | int | str | dict], 
    currency: str = '€') -> str:
    """
    Format a list of values as currency based on the specified currency type.

    Args:
        values: A list of float, int, or str values to format.
        currency: The currency type ('EUR' or 'GBP').

    Returns:
        A string with the formatted currency values.
    """
    result = []
    for value in values:
        if isinstance(value, (float, int)):
            result.append(f"{currency}{value:,.2f}")
        elif isinstance(value, dict):
            # Assuming the dict contains a 'value' key for formatting
            value['value'] = f"{currency}{value.get('value', 0):,.2f}"
            result.append(value)
        else:
            result.append(value)
    return result


def get_set_total_items(items: list = ['Tot', '%', 'Lst Yr'], **kwargs) -> list:
    """
    Get the total items for a set of bookings.

    Args:
        attribute: A tuple of attribute names to retrieve or a callable function.

    Returns:
        A list with total items.
    """
    set_items(items, **kwargs)
    return [[] for _ in range(len(items))]


def split_by_location(bookings: list[Booking], **kwargs) -> dict:
    locations = {}

    for booking in bookings:
        location = booking.property.address.generalLocation
        if location not in locations.keys():
            locations[location] = []
        locations[location].append(booking)
    
    set_items(['ALL'] + list(locations.keys()), **kwargs)
    return [bookings] + list(locations.values())


def split_by_owner_guest(bookings: list[Booking], **kwargs) -> dict:
    lists = [bookings, [], []]
    for booking in bookings:
        if booking.details.isOwner:
            lists[1].append(booking)
        else:
            lists[2].append(booking)

    set_items(['Total', 'Owner', 'Guest'], **kwargs)
    return lists


def split_by_booking_source(bookings: list[Booking], **kwargs) -> dict:
    sources = {'Direct': [], 'Airbnb': [], 'Booking.com': [], 'Vrbo': []}

    for booking in bookings:
        source = booking.details.enquirySource
        if source not in sources:
            sources[source] = []
        sources[source].append(booking)

    set_items(['Total'] + list(sources.keys()), **kwargs)
    return [bookings] + list(sources.values())


def set_month_rows(table: Table) -> None:
    style = Stylesheet()
    style.bold = True
    style.fontSize = 10
    for month in dates.stringMonths():
        table.row(name=month, style=style)
    table.row(name='TOTAL', style=style)


def get_year_comparison_dict(thisYear: int, lastYear: int) -> dict:
    """
    Create a dictionary for year comparison.

    Args:
        thisYear: Total for the current year.
        lastYear: Total for the previous year.

    Returns:
        A dictionary with the comparison values.
    """
    versus = thisYear - lastYear
    color = 'f10d0c' if versus < 0 else '069a2e' if versus > 0 else '000000'
    return {'value': versus, 'styles': {'color': color}}


def get_percentage(x: int, y: int | None) -> str:
    """
    Create a dictionary for percentage representation.

    Args:
        value: The percentage value as a string.

    Returns:
        A dictionary with the percentage value.
    """
    if y is None:
        return '100%'
    if y == 0:
        return '-'
    return f"{x / y * 100:.0f}%"


def get_year_totals(
    bookings: list[Booking], 
    calcFunc: callable, 
    dateAttrs: list = ['arrival'], 
    **kwargs) -> dict:
    """
    Calculate total gross and nights for a list of bookings by year.

    Args:
        bookings: A list of Booking objects.
        attribute: A tuple of attribute names to retrieve.

    Returns:
        A dictionary with total gross and nights by year.
    """
    years = [0, 0]
    for booking in bookings:
        value = calcFunc(booking)
        if isinstance(value, bool):
            value = int(value)
        date = get_date_attribute(booking, dateAttrs)
        if date is None:
            #logbooking(booking, f"No date found with '{dateAttrs}'")
            continue
        if date.year == dates.year():
            years[0] += value
        elif date.year == dates.year(-1):
            years[1] += value
    return years


def set_items(
    items, 
    **kwargs: dict[str: Worksheet | Table | Table.Column]) -> None:
    """
    Set items in a worksheet, table, or column.
    
    Args:
        items: A list of items to set.
        kwargs: Keyword arguments for the worksheet, table, or column.
    """
    worksheet: Worksheet = kwargs.get('worksheet', None)
    if worksheet:
        for item in items:
            worksheet.table(name=item)
        return
    table: Table = kwargs.get('table', None)
    if table:
        for item in items:
            table.column(name=item)
        return
    column: Table.Column = kwargs.get('column', None)
    if column:
        for item in items:
            column.subcolumn(name=item)


def split_by_month(
    bookings: list[Booking], 
    dateAttrs: list = ['arrival'], **kwargs) -> dict:
    """
    Split bookings by month.
    Args:
        bookings: A list of Booking objects.
    Returns:
        A list of lists, where each inner list contains bookings for a specific
        month.
    """
    # Set up a list for each month (1-12) plus a total at the end
    # Each inner list will hold bookings for that month
    # The last list will hold all bookings as a total
    result = [[] for _ in range(12)]
    for booking in bookings:
        date = get_date_attribute(booking, dateAttrs)
        if date is None:
            continue
        result[date.month - 1].append(booking)

    result += [bookings]  # Add total bookings at the end
    return result


def split_by_year(
    bookings: list[Booking], 
    dateAttrs: list = ['arrival'], 
    **kwargs) -> dict:
    """
    Split bookings by year.

    Args:
        bookings: A list of Booking objects.
        dateAttrs: A list of date attribute names to use for splitting.
        **kwargs: Additional keyword arguments.

    Returns:
        A list of lists, where each inner list contains bookings for the current
        year and the previous year, respectively.
    """
    years = [[], []]

    for booking in bookings:
        date = get_date_attribute(booking, dateAttrs)
        if date is None:
            continue
        if date.year == dates.year():
            years[0].append(booking)
        elif date.year == dates.year(-1):
            years[1].append(booking)

    return years


def get_date_attribute(booking: Booking, dateAttrs: list) -> datetime.date:
    """
    Get the specified date attribute from a Booking object.

    Args:
        booking: A Booking object.
        dateAttrs: The name of the date attribute to retrieve.

    Returns:
        The value of the specified date attribute.
    """
    for attr in dateAttrs:
        if hasattr(booking, attr):
            booking = getattr(booking, attr)
        else:
            raise AttributeError(f"Booking does not have an attribute '{attr}'")
    return booking