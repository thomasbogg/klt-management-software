from csv import DictWriter
import datetime

from default.dates import dates
from default.property.prices import Prices
from default.settings import LOCAL_STORAGE_DIR
from utils import set_euro_currency
from web.html import HTML
from workbooks.utils import set_tables_in_worksheet
from workbooks.workbook import Workbook
from workbooks.workbook import Worksheet


CACHE_DIRECTORY = f'{LOCAL_STORAGE_DIR}/prices/'


def set_html_price_table(prices: Prices) -> str:
    """
    Generate an HTML table from the prices data.

    :param prices: Prices object containing price data.
    
    :return: HTML string representing the price table.
    """
    html = _get_html_price_table_header()
    html += _get_html_table_start()

    for month in range(1, 14):
        monthName = dates.prettyMonth(month) if month < 13 else 'Festive Holiday Period'
        weeklyRate = prices.month(month)
        monthlyRate = None

        if not weeklyRate:
            continue
       
        if month in (1, 11, 12):
            monthlyRate = prices.earlyWinterMonthlyRate
        elif month in (2, 3):
            monthlyRate = prices.lateWinterMonthlyRate

        if monthlyRate is not None:
            monthlyRate = set_euro_currency(monthlyRate, decimalPlaces=0)
        else:
            monthlyRate = '-'

        weeklyRate = set_euro_currency(weeklyRate, decimalPlaces=0)
        html = _set_html_price_table_row(
            html,
            month,
            monthName,
            weeklyRate,
            monthlyRate
        )

    html += _get_html_table_end()

    filename = f'{CACHE_DIRECTORY}website/{prices.year}-prices-' \
               f'{prices.name}-for-web.html'
   
    with open(filename, 'w') as file:
        html = HTML(html).prettify()
        file.write(html)


def set_PIMS_price_table(prices: Prices) -> None:
    """
    Generate a PIMS-compatible price table from the prices data.

    :param prices: Prices object containing price data.
    
    :return: String representing the PIMS price table.
    """
    filename = f'{CACHE_DIRECTORY}PIMS/{prices.year}-' \
               f'prices-for-PIMS-{prices.name}.csv'
    fieldnames=[
        'PID', 
        'Code', 
        'start', 
        'end', 
        'weekly', 
        'changeover', 
        'minstay'
    ]
    with open(filename, 'w', newline='') as csvfile:
        writer = DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for month in range(1, 14):
            for year in range(prices.year, prices.year + 2):
                month_start, month_end = _get_month_start_end(month, year)
                writer.writerow(
                    {
                        'PID': 0, 
                        'Code': 0, 
                        'start': month_start, 
                        'end': month_end, 
                        'weekly': prices.month(month), 
                        'changeover': 9, 
                        'minstay': 4
                    }
                )


def set_prices_workbook(prices: list[Prices]) -> None:
    """
    Generate a platform-compatible price table from the prices data.

    :param prices: list of Prices objects containing price data.
    
    :return: None
    """
    filename = f'prices-for-{prices[0].year}.xlsx'
    workbook = Workbook(filename, CACHE_DIRECTORY)
    workbook.create()
    enquirySources = {
        'Direct': {'no change': 1},
        'Airbnb': {'days': 7, 'commission at 3%': .03}, 
        'Booking.com': {'days': 7, 'commission at 18%': .82, 'genius at 22%': .78},
        'Vrbo': {'days': 7, 'commission at 8%': .92},
    }
    _set_enquiry_sources_sheets_in_workbook(workbook, prices, enquirySources)
    _set_winter_rates_in_workbook(workbook, prices)
    for sheet in workbook.sheets:
        set_tables_in_worksheet(sheet, sheet.tables, adjustColumnWidths=False)
    workbook.save()


def _get_html_price_table_header() -> str:
    """
    Generate the header for the HTML price table.

    :return: HTML string for the table header.
    """
    return '<p>*' \
           '<i>An administration charge of 5.5% will be added to the prices below</i>' \
           '</p>' \
           '<p>*' \
           '<i>Option to pay in Pounds Sterling (£) available, please ask for quote with your enquiry</i>' \
           '</p>' \
           '<p>*' \
           '<i>For the Winter Monthly Rates, please ask with your enquiry</i>' \
           '</p>' \


def _get_html_table_start() -> str:
    """
    Generate the starting HTML for the price table.

    :return: HTML string to start the table.
    """
    return '<table data-tablestyle="MsoTableGrid" data-tablelook="1696" aria-rowcount="13">' \
           '<tbody>' \
           '<tr aria-rowindex="1">' \
           '<td data-celllook="0">' \
           '<b><span data-contrast="auto">Period</span></b>' \
           '</td>' \
           '<td style="text-align: center;" data-celllook="0">' \
           '<b><span data-contrast="auto">Yearly Weekly Rate</span></b>' \
           '</td>' \
           '<td style="text-align: center;" data-celllook="0">' \
           '<b><span data-contrast="auto">Winter Monthly Rate</span></b>' \
           '</td>' \
           '</tr>'


def _set_html_price_table_row(
        html: str,
        month: int,
        monthName: str,
        weeklyRate: float,
        monthlyRate: float = None) -> str:
    """ 
    Set a row in the HTML price table.
    
    :param html: Current HTML string.
    :param month: Month number (1-13).
    :param monthName: Name of the month.
    :param weeklyRate: Weekly rate for the month.
    :param monthlyRate: Monthly rate for the month, if applicable.  
    
    :return: Updated HTML string with the new row.
    """
    html += f'<tr aria-rowindex="{month + 1}">'
    html += '<td data-celllook="0">'
    html += f'<span data-contrast="auto">{monthName}</span>'
    html += '</td>'
    html += f'<td style="text-align: center;" data-celllook="0">'
    html += f'<span data-contrast="auto">{weeklyRate}</span>'
    html += '</td>'
    html += f'<td style="text-align: center;" data-celllook="0">'
    html += f'<span data-contrast="auto">{monthlyRate}</span>'
    html += '</td>'
    html += '</tr>'
    return html


def _get_html_table_end() -> str:
    """
    Generate the ending HTML for the price table.

    :return: HTML string to end the table.
    """
    return '</tbody>' \
           '</table>'


def _get_month_start_end(
        month: int, 
        year: int = dates.year()) -> tuple[datetime.date, datetime.date]:
    """
    Get the start and end dates for a given month and year.

    :param month: Month number (1-12).
    :param year: Year number.

    :return: Tuple containing start and end dates of the month.
    """
    startMonth, endMonth = month, month
    
    if month == 1:
        startDay = 3
    elif month == 13:
        startMonth = 12
        startDay = 24
    else:
        startDay = 1
   
    start = dates.date(year, startMonth, startDay)
   
    if month == 12:
        daysInMonth = 23
    elif month == 13:
        year += 1
        endMonth = 1
        daysInMonth = 2
    else:
        daysInMonth = dates.daysInMonth(year, month)

    end = dates.date(year, endMonth, daysInMonth)
    return start, end


def _set_enquiry_sources_sheets_in_workbook(
        workbook: Workbook, 
        prices: list[Prices], 
        enquirySources: dict) -> None:
    """
    Set the enquiry sources sheets in the workbook.
    
    :param workbook: The workbook to add the sheets to.
    :param prices: List of Prices objects containing price data.
    :param enquirySources: Dictionary containing enquiry sources and their fees.
    
    :return: None
    """
    for platform, fees in enquirySources.items():
        sheet = workbook.newSheet(platform)
        table = sheet.table()
        data = list()
    
        for month in dates.stringMonths():
            table.row(name=month)
        table.row(name='Festive')

        for price in prices:
            table.column(name=price.name)

            priceData = list()
            for month in range(1, 14):
                value = price.month(month)

                if not value:
                    priceData.append('-')
                    continue

                for fee in fees.values():
                    value /= fee

                intValue = int(value)
                strValue = set_euro_currency(intValue, decimalPlaces=0)
                priceData.append(strValue)

            data.append(priceData)
        table.data = data


def _set_winter_rates_in_workbook(workbook: Workbook, prices: list[Prices]) -> None:
    """
    Set the winter rates sheet in the workbook.

    :param workbook: The workbook to add the sheet to.
    :param prices: List of Prices objects containing winter rates.

    :return: None
    """
    def __build_table(
            sheet: Worksheet, 
            tableName: str, 
            prices: list[Prices], 
            rateAttr: str, 
            compAttr: str) -> None:
        """
        Set the data in the worksheet table.

        :param sheet: The worksheet to set the table in.
        :param table: The table to set the data for.
        :param data: The data to populate the table with.

        :return: None
        """
        table = sheet.table(name=tableName)
        table.row(name='Rate')
        table.row(name='Daily')
        table.row(name='Effective Discount')
        data = list()
        for price in prices:
            table.column(name=price.name)
            monthlyRate = getattr(price, rateAttr)
            monthlyDailyRate = monthlyRate // 31 + 1
            _comp = getattr(price, compAttr)
            discount = __get_effective_monthly_rate(
                monthlyDailyRate,
                _comp
            )
            data.append([
                set_euro_currency(monthlyRate), 
                set_euro_currency(monthlyDailyRate, 0), 
                discount
            ])
        table.data = data

    def __get_effective_monthly_rate(monthlyDailyRate: float, weeklyRate: float) -> str:
        """
        Calculate the effective monthly rate based on the price, days, and weeks.

        :param price: The price to calculate the effective monthly rate from.
        :param days: The number of days in the month.
        :param weeks: The number of weeks in the month.

        :return: The effective monthly rate.
        """
        if not monthlyDailyRate or not weeklyRate:
            return '-'
        weeklyDailyRate = weeklyRate / 7
        difference = (1 - (monthlyDailyRate / weeklyDailyRate)) * 100
        return f'{difference:.0f}%'

    sheet = workbook.newSheet('Winter Rates')
    __build_table(sheet, 'Early Winter Rates', prices, 'earlyWinterMonthlyRate', 'december')
    __build_table(sheet, 'Late Winter Rates', prices, 'lateWinterMonthlyRate', 'february')