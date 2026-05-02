from correspondence.owner.functions import new_owner_email
from default.database.database import Database
from default.database.functions import get_database, get_property, search_properties
from default.google.mail.functions import send_email
from default.property.prices import Prices
from default.settings import WEBSITE_LINK
from default.dates import dates
from default.update.wrapper import update
from prices.functions import (
    set_html_price_table, 
    set_PIMS_price_table, 
    set_prices_workbook,
)


CACHE_DIRECTORY = 'cache/prices/'


@update
def update_prices_for_year(
    name: str = None,
    year: int = dates.year(1), 
    yearlyChange: float = .1, 
    winterChange: float = .05,
    emailOwners: bool = False) -> None:
    """
    Update the prices for a specific year with a given change percentage.

    :param year: The year for which to update the prices.
    :param change: The percentage change to apply to the prices.

    :return: Success message indicating the prices were updated.
    """
    prevPrices = _get_year_prices(year=year - 1, name=name)
    newPrices = []
    database = get_database()
    updatedPrices = []

    for price in prevPrices:
        newPrice = Prices(database)
        newPrice.name = price.name
        newPrice.year = year
        updatedPrices.append(newPrice.name)
       
        for month in range(1, 14):
            value = _get_new_price(price.month(month), yearlyChange)
            newPrice.setMonth(month, value)

        for winterRate in ('earlyWinterMonthlyRate', 'lateWinterMonthlyRate'):
            value = _get_new_price(getattr(price, winterRate), winterChange)
            setattr(newPrice, winterRate, value)

        if newPrice.exists():
            newPrice.update()
        else:
            newPrice.insert()
       
        newPrices.append(newPrice)

    set_price_tables(year)
    if emailOwners:
        email_owners_with_new_prices(database, updatedPrices, year, yearlyChange)
    database.close()
    return f'Prices updated for {year} with a change of {yearlyChange * 100}%.'


@update
def update_a_price(name=None, year=None, **monthsPrices) -> None:
    """
    Update a specific price tier for a given year.

    :param name: The name of the price tier to update.
    :param year: The year for which to update the price tier.
    :param monthsPrices: A dictionary containing month names as keys and their corresponding prices as values.

    :return: Success message indicating the price tier was updated.
    """
    if name is None:
        return 'No name given for updating prices'
    if year is None:
        return 'No year given for updating prices'

    prices = _get_year_prices(year, name, closeDatabase=False)
    if not prices:
        return f'No prices found for year {year} with name {name}.'
    
    prices = prices[0]

    for month, price in monthsPrices.items():
        prices.setMonth(month, price)

    prices.update()
    prices.database.close()
    set_price_tables(year)
    return f'Successfully updated price tier {name} for year {year}.'


@update
def new_price_tier(name = None, prices: list[float] = None, year: int = dates.year(1), propertyNames: list[str] = None):
    """
    Create a new price tier.

    :param name: The name of the price tier.
    :param prices: A list of prices associated with the price tier.
    :param year: The year for the price tier.
    :param propertyNames: A list of property names associated with the price tier.

    :return: A new Prices object representing the price tier.
    """
    if name is None:
        return 'No name given for new prices'
    if propertyNames is None:
        return 'No property names given for new prices'

    database = get_database()
    priceTier = Prices(database)
    priceTier.name = name
    priceTier.year = year
    for i in range(1, 14):
        priceTier.setMonth(i, prices[i - 1])
    if len(prices) > 13:
        priceTier.earlyWinterMonthlyRate = prices[13]
    if len(prices) > 14:
        priceTier.lateWinterMonthlyRate = prices[14]

    if priceTier.exists():
        priceTier.update()
        id = priceTier.id
    else:
        id = priceTier.insert()

    for propertyName in propertyNames:
        property = get_property(name=propertyName).fetchone()
        property.priceId = id
        property.update()

    database.close()
    set_price_tables(year)
    return 'Successfully added new price tier to database!'


def _get_year_prices(year: int = dates.year(-1), name: str = None, closeDatabase: bool = True) -> list[Prices]:
    """
    Get the prices for the previous year.

    :param prices: Prices object containing current year data.
    
    :return: Prices object for the previous year.
    """
    search = Database(loadObject=Prices)
    search.connect()
    search.propertyPrices.isPrimaryTable = True
    search.propertyPrices.select().all()
    search.propertyPrices.where().year().isEqualTo(year)
    if name:
        search.propertyPrices.where().name().isEqualTo(name)
    results = search.fetchall()
    if closeDatabase:
        search.close()
    return results


def set_price_tables(year: int = dates.year(1)) -> None:
    """
    Set the price tables for the given prices.

    :param prices: A list of Prices objects to set the tables for.
    """
    prices = _get_year_prices(year)
    set_prices_workbook(prices)
    for price in prices:
        set_html_price_table(price)
        set_PIMS_price_table(price)


def _get_new_price(value: float, change: float) -> float:
    """
    Calculate the new price after applying the change.

    :param value: Current price value.
    :param change: Percentage change to apply.

    :return: New price after applying the change.
    """
    value = int(value * (1 + change))
    while value % 5 != 0:
        value += 1
    return value


@update
def email_owners_with_new_prices(year: int = dates.year(1)) -> None:
    """
    Email owners with the new prices for the given year.

    :param year: The year for which to email the owners.
    """
    newYearPrices = _get_year_prices(year)
    prevYearPrices = _get_year_prices(year - 1)
    for newPrice in newYearPrices:

        prevPrice = [prevPrice for prevPrice in prevYearPrices if prevPrice.name == newPrice.name]
        if not prevPrice:
            continue
        
        search = search_properties()

        select = search.propertyOwners.select()
        select.name()
        select.email()

        where = search.properties.where()
        where.priceId().isEqualTo(newPrice.name)
        where.weBook().isEqualTo(True)

        properties = search.fetchall()
        search.close()
        if not properties:
            continue

        for property in properties:
            subject = f'New Prices Set for {year} - {property.name}'
            user, message = new_owner_email(subject=subject, property=property)

            body = message.body

            body.paragraph(
                'I hope this email finds you well.'
            )
            body.paragraph(
                'I am writing to inform you that the weekly prices for your property',
                f'{property.name} have been updated for the year {year}.'
            )
            body.paragraph(
                'You can see the new weekly prices and the change in the table below:'
            )
            body.table(
                rows=_email_price_table_data(newPrice, prevPrice[0])
            )
            body.paragraph(
                '* Early Winter Monthly rate applies to stays of 28 nights or longer',
                'from November to January.',
            )
            body.paragraph(
                '** Late Winter Monthly rate applies to stays of 28 nights or longer',
                'from February to March.',
            )
            body.paragraph(
                'I trust this has been helpful. If you have questions or concerns',
                'please do not hesitate to contact me.'
            )

            send_email(user=user, message=message)

    return f'Email notifications sent to owners with new prices for {year}.'


def _email_price_table_data(newPrice: Prices, prevPrice: Prices) -> list[list]:
    """
    Generate the data for the email price table.

    :param price: The Prices object containing the price data.

    :return: A list of lists representing the table data.
    """
    headers = ['Month', 'Prev. Price', 'New Price', 'Change']
    data = [headers]
    months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December',
        'Festive', '*Early Winter Monthly', '**Late Winter Monthly'
    ]
    for i in range(1, 16):
        monthName = months[i - 1]
        previousYear = prevPrice.month(i)
        newYear = newPrice.month(i)
        change = newYear - previousYear
        changeStr = f'+€{change}' if change > 0 else str(change)
        row = [monthName, f'€{previousYear}', f'€{newYear}', f'{changeStr}']
        data.append(row)
    return data