import datetime
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from typing import List, Self

from default.browser.browser import KLTBrowser
from default.dates import dates
from default.settings import (
    PIMS_PASSWORD,
    PIMS_USERNAME,
    PLATFORMS
)
from utils import string_to_float
from web.html import HTML


class BrowsePIMS(KLTBrowser):
    """
    Browser interface for PIMS holiday rental management system.
    
    Provides methods for navigating, logging in, and interacting with 
    PIMS web interface, including reservations list and order forms.
    
    Attributes:
        url: Base URL for PIMS system
    """
    url = 'https://holidayrentalmanagement.com/pimsv18.0'
    
    def __init__(self, visible: bool = False):
        """
        Initialize PIMS browser interface.
        
        Parameters:
            visible: Whether to show the browser window
        """
        super().__init__('PIMS', visible)
        self._reservationsList = self.ReservationsList(self.url, self._driver)
        self._orderForms = self.OrderForms(self.url, self._driver)

    def goTo(self, url: str | None = None) -> 'BrowsePIMS':
        """
        Navigate to specified URL or default PIMS URL.
        
        Parameters:
            url: URL to navigate to, or None for default PIMS URL
            
        Returns:
            Self for method chaining
        """
        if url is None: 
            url = self.url
        return super().goTo(url, wait=1.3)
    
    def login(self) -> 'BrowsePIMS':
        """
        Log into PIMS using credentials from settings.
        
        Returns:
            Self for method chaining
        """
        try: 
            self.element(By.NAME, 'email').input(PIMS_USERNAME)
        except NoSuchElementException: 
            return self
        self.element(By.NAME, 'pw').input(PIMS_PASSWORD)
        self.element(By.NAME, 'login0').enter(wait=2)
        return self

    @property
    def reservations(self) -> 'BrowsePIMS.ReservationsList':
        """Get the reservations list interface."""
        return self._reservationsList

    @property
    def orderForms(self) -> 'BrowsePIMS.OrderForms':
        """Get the order forms interface."""
        return self._orderForms

    class ReservationsList(KLTBrowser):
        """
        Interface for PIMS reservations list.
        
        Provides methods for viewing, filtering and interacting with 
        reservation listings.
        """
        def __init__(self, url: str, driver):
            """
            Initialize reservations list interface.
            
            Parameters:
                url: Base URL for PIMS system
                driver: Browser driver instance
            """
            self._url = url
            self._driver = driver
            self._wait = WebDriverWait(self._driver, 10)

        def goTo(self) -> 'BrowsePIMS.ReservationsList':
            """
            Navigate to the reservations list page.
            
            Returns:
                Self for method chaining
            """
            return super().goTo(f'{self.url}/orderlist.php')
        
        def update(self) -> 'BrowsePIMS.ReservationsList':
            """
            Update the reservations list with current filter settings.
            
            Returns:
                Self for method chaining
            """
            self.element(By.NAME, 'run').enter(wait=2)
            return self
        
        @property
        def list(self) -> dict:
            """
            Get parsed reservation data from the current page.
            
            Returns:
                Dictionary of parsed reservation data
            """
            parser = HTML(self.html, 'table', 'class', 'orderlisting')
            self._parse_reservations_rows(parser, parser.tableRows()[1:])
            return parser.parsed
        
        @property
        def url(self) -> str:
            """Get the base URL for PIMS."""
            return self._url

        @property
        def propertyName(self) -> str:
            """Get the currently selected property name."""
            return self.element(By.NAME, 'property_selected').option

        @propertyName.setter
        def propertyName(self, name: str | None = None) -> 'BrowsePIMS.ReservationsList':
            """
            Set the property filter by name.
            
            Parameters:
                name: Property name to filter by
                
            Returns:
                Self for method chaining
            """
            self.element(By.NAME, 'property_selected').selectByVisibleText(str(name))
            return self
        
        @property
        def start(self) -> datetime.date:
            """Get the current start date filter."""
            return self._get_date('first_start')

        @start.setter
        def start(self, date: datetime.date) -> 'BrowsePIMS.ReservationsList':
            """
            Set the start date filter.
            
            Parameters:
                date: Start date to filter from
                
            Returns:
                Self for method chaining
            """
            self._set_date(date, 'first_start')
            return self
    
        @property
        def end(self) -> datetime.date:
            """Get the current end date filter."""
            return self._get_date('last_start')

        @end.setter
        def end(self, date: datetime.date) -> 'BrowsePIMS.ReservationsList':
            """
            Set the end date filter.
            
            Parameters:
                date: End date to filter to
                
            Returns:
                Self for method chaining
            """
            self._set_date(date, 'last_start')
            return self

        @property
        def updatedSince(self) -> datetime.date:
            """Get the 'updated since' date filter."""
            return self._get_date('update')

        @updatedSince.setter
        def updatedSince(self, date: datetime.date) -> 'BrowsePIMS.ReservationsList':
            """
            Set the 'updated since' date filter.
            
            Parameters:
                date: Datetime.date to filter updates from
                
            Returns:
                Self for method chaining
            """
            return self._set_date(date, 'update')

        @property
        def resultsType(self) -> str:
            """Get the current results type filter."""
            return self.element(By.NAME, 'ordertype').option

        @resultsType.setter
        def resultsType(self, _type: str) -> 'BrowsePIMS.ReservationsList':
            """
            Set the results type filter.
            
            Parameters:
                _type: Type of results to show
                
            Returns:
                Self for method chaining
            """
            self.element(By.NAME, 'ordertype').selectByVisibleText(str(_type))
            return self

        @property
        def sortBy(self) -> str:
            """Get the current sort field."""
            return self.element(By.NAME, 'sortfield').option

        @sortBy.setter
        def sortBy(self, method: str) -> 'BrowsePIMS.ReservationsList':
            """
            Set the sort field.
            
            Parameters:
                method: Field to sort by
                
            Returns:
                Self for method chaining
            """
            self.element(By.NAME, 'sortfield').selectByValue(method)
            return self

        @property
        def iCalOnly(self) -> bool:
            """Get whether only iCal imports are shown."""
            return self.element(By.NAME, 'iCalImports').isChecked

        @iCalOnly.setter
        def iCalOnly(self, iCal: bool = False) -> 'BrowsePIMS.ReservationsList':
            """
            Set whether to show only iCal imports.
            
            Parameters:
                iCal: True to show only iCal imports
                
            Returns:
                Self for method chaining
            """     
            if self.iCalOnly:
                if not iCal: 
                    self.element(By.NAME, 'iCalImports').click(wait=1.5)
            else:
                if iCal: 
                    self.element(By.NAME, 'iCalImports').click(wait=1.5)
            return self

        @property
        def onlyOwner(self) -> bool:
            """Get whether only owner bookings are shown."""
            return self.element(By.NAME, 'Oowner_booking').isChecked

        @onlyOwner.setter
        def onlyOwner(self, owner: bool = False) -> 'BrowsePIMS.ReservationsList':
            """
            Set whether to show only owner bookings.
            
            Parameters:
                owner: True to show only owner bookings
                
            Returns:
                Self for method chaining
            """
            if self.onlyOwner:
                if not owner: 
                    self.element(By.NAME, 'Oowner_booking').click(wait=1.5)
            else:
                if owner: 
                    self.element(By.NAME, 'Oowner_booking').click(wait=1.5)
            return self

        @property
        def noOwner(self) -> bool:
            """Get whether owner bookings are excluded."""
            return self.element(By.NAME, 'Xowner_booking').isChecked
                    
        @noOwner.setter
        def noOwner(self, noOwner: bool = False) -> 'BrowsePIMS.ReservationsList':
            """
            Set whether to exclude owner bookings.
            
            Parameters:
                noOwner: True to exclude owner bookings
                
            Returns:
                Self for method chaining
            """
            if self.noOwner:
                if not noOwner: 
                    self.element(By.NAME, 'Xowner_booking').click(wait=1.5)
            else:
                if noOwner: 
                    self.element(By.NAME, 'Xowner_booking').click(wait=1.5)
            return self

        def _set_date(self, date: datetime.date, name: str) -> 'BrowsePIMS.ReservationsList':
            """
            Set a date field in the form.
            
            Parameters:
                date: The date to set
                name: Name of the date field
                
            Returns:
                Self for method chaining
            """
            year, month, day = dates.breakUpDate(date)
            self.element(By.XPATH, f'//select[@id="{name}_date_Month_ID"]').selectByValue(str(month - 1))
            self.element(By.XPATH, f'//select[@id="{name}_date_Day_ID"]').selectByVisibleText(str(day))
            self.element(By.ID, f"{name}_date_Year_ID").clear().input(str(year), time=.1)
            return self
        
        def _get_date(self, name: str) -> datetime.date:
            """
            Get a date from a form field.
            
            Parameters:
                name: Name of the date field
                
            Returns:
                Date object from the field values
            """
            month = self.element(By.XPATH, f'//select[@id="{name}_date_Month_ID"]').option
            day = self.element(By.XPATH, f'//select[@id="{name}_date_Day_ID"]').option
            year = self.element(By.ID, f"{name}_date_Year_ID").attribute('value')
            return dates.date(year, month, day)
        
        def _parse_reservations_rows(self, parser: HTML, rows: list) -> 'BrowsePIMS.ReservationsList':
            """
            Recursively parse rows of reservation data.
            
            Parameters:
                parser: HTML object to use
                rows: List of rows to parse
                
            Returns:
                Self for method chaining
            """
            if not rows:
                return self
            row = rows.pop()
            data = parser.rowData(row, includeHeader=False)
            parser.parsed = {
                'orderId': int(data[0].text.strip()),
                'guest': data[2].text.strip(),
                'arrival': self._convert_to_date(data[3].text.strip().split()[1:]),
                'departure': self._convert_to_date(data[4].text.strip().split()[1:]),
                'enquiry': self._convert_to_date(data[5].text.strip().split()),
                'status': data[8].text.strip()
            }
            return self._parse_reservations_rows(parser, rows)

        def _convert_to_date(self, dateList: List[str] = None) -> datetime.date:
            """
            Convert date strings to date object.
            
            Parameters:
                dateList: List of date strings [day, month, year]
                
            Returns:
                Date object
            """
            if not isinstance(dateList, list): 
                dateList = dateList.split()
            if len(dateList) == 3: 
                day, month, year = dateList
            else: 
                weekday, day, month, year = dateList
            return dates.date(year, month, day)
        
        def __str__(self) -> str:
            """
            Get string representation of reservations list.
            
            Returns:
                Formatted string showing all reservations
            """
            string = '\n\t\t_____RESERVATIONS_____'
            for reservation in self.list:
                string += f'\n\t\t{reservation}'
            return string
        
        def quit(self) -> None:
            """Close the browser session."""
            return self._driver.quit()
        

    class OrderForms(KLTBrowser):
        """
        Interface for PIMS order forms.
        
        Provides methods for viewing and editing booking details including
        guest info, dates, charges, and custom fields.
        """
        def __init__(self, url: str, driver):
            """
            Initialize order forms interface.
            
            Parameters:
                url: Base URL for PIMS system
                driver: Browser driver instance
            """
            self._url = url
            self._driver = driver
            self._wait = WebDriverWait(self._driver, 10)

        def goTo(self, id: str | int) -> 'BrowsePIMS.OrderForms':
            """
            Navigate to a specific order form by ID.
            
            Parameters:
                id: Order ID to navigate to
                
            Returns:
                Self for method chaining
            """
            super().goTo(f'{self._url}/orderform.php?formtype=open&order_id={id}')
            self.scroll()
            return self

        def element(self, mode: By, value: str, ) -> Self:
            """
            Find an element by its mode and value.
            
            Args:
                mode: The mode to find the element (e.g., ID, XPATH).
                value: The value to find the element.
                
            Returns:
                The current instance of the Browser class.
            """
            self._element = self._driver.find_element(mode, value)
            return self
        
        def update(self) -> 'BrowsePIMS.OrderForms':
            """
            Save changes to the current order form.
            
            Returns:
                Self for method chaining
            """
            self.element(By.XPATH, "//input[@value='Update']").click(wait=2)
            return self

        def cancelBooking(self) -> 'BrowsePIMS.OrderForms':
            """
            Cancel the current booking.
            
            Returns:
                Self for method chaining
            """
            self.element(By.LINK_TEXT, 'Cancel this reservation...').click(wait=2)
            self.element(By.CLASS_NAME, 'Button').click(wait=2)
            return self

        def deleteBooking(self) -> 'BrowsePIMS.OrderForms':
            """
            Delete the current booking from the database.
            
            Returns:
                Self for method chaining
            """
            self.element(By.LINK_TEXT, 'Delete this reservation from the database...').click(wait=2)
            self.element(By.CLASS_NAME, 'Button').click(wait=2)
            return self
        
        @property
        def propertyName(self) -> str:
            """Get the property name for this booking."""
            return self._by_selection('property_id')
        
        @propertyName.setter
        def propertyName(self, name: str) -> 'BrowsePIMS.OrderForms':
            """
            Set the property for this booking.
            
            Parameters:
                name: Property name to set
                
            Returns:
                Self for method chaining
            """
            return self._by_selection('property_id', name)
        
        @property
        def enquiryStatus(self) -> str | None:
            """Get the current enquiry status."""
            for _class in ('statusbar_current', 'statusbar_isopen', 'statusbar_endpoint'):
                try: 
                    return self.element(By.CLASS_NAME, _class).text
                except: 
                    continue 
            return None

        @property
        def propertyIsArchived(self) -> bool:
            """Check if the property is archived."""
            return self.hasElement(By.XPATH, '//h2[contains(., "has been archived")]')
        
        @property
        def enquiryDate(self) -> datetime.date:
            """Get the enquiry date."""
            return self._convert_to_date(self._by_field('order_date'))
        
        @enquiryDate.setter
        def enquiryDate(self, date: datetime.date | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the enquiry date.
            
            Parameters:
                date: New enquiry date, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field('order_date', value=date)
        
        @property
        def arrivalDate(self) -> datetime.date:
            """Get the arrival date."""
            return self._convert_to_date(self._by_field('start_date'))
        
        @arrivalDate.setter
        def arrivalDate(self, date: datetime.date | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the arrival date.
            
            Parameters:
                date: New arrival date, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field('start_date', value=date)

        @property
        def departureDate(self) -> datetime.date:
            """Get the departure date."""
            return self._convert_to_date(self._by_field('end_date'))

        @departureDate.setter
        def departureDate(self, date: datetime.date | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the departure date.
            
            Parameters:
                date: New departure date, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field('end_date', value=date)
        
        @property
        def arrivalTime(self) -> str:
            """Get the arrival time."""
            return dates.time(self.arrivalHour, self.arrivalMinute)

        @property
        def arrivalHour(self) -> str:
            """Get the arrival hour."""
            return self._by_selection('start_time_HH')
        
        @arrivalHour.setter
        def arrivalHour(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the arrival hour.
            
            Parameters:
                value: Hour value as string, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_selection('start_time_HH', value=value)

        @property
        def arrivalMinute(self) -> str:
            """Get the arrival minute."""
            return self._by_selection('start_time_MM')

        @arrivalMinute.setter
        def arrivalMinute(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the arrival minute.
            
            Parameters:
                value: Minute value as string, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_selection('start_time_MM', value=value)
        
        @property
        def departureTime(self) -> str:
            """Get the departure time."""
            return dates.time(self.departureHour, self.departureMinute)
        
        @property
        def departureHour(self) -> str:
            """Get the departure hour."""
            return self._by_selection('end_time_HH')
        
        @departureHour.setter
        def departureHour(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the departure hour.
            
            Parameters:
                value: Hour value as string, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_selection('end_time_HH', value=value)

        @property
        def departureMinute(self) -> str:
            """Get the departure minute."""
            return self._by_selection('end_time_MM')
        
        @departureMinute.setter
        def departureMinute(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the departure minute.
            
            Parameters:
                value: Minute value as string, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_selection('end_time_MM', value=value)

        @property
        def adults(self) -> int:
            """Get the number of adults."""
            return int(self._by_field('party_size_adults'))
        
        @adults.setter
        def adults(self, value: int | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the number of adults.
            
            Parameters:
                value: Number of adults, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field('party_size_adults', value=value)

        @property
        def children(self) -> int:
            """Get the number of children."""
            return int(self._by_field('party_size_children'))
        
        @children.setter
        def children(self, value: int | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the number of children.
            
            Parameters:
                value: Number of children, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field('party_size_children', value=value)

        @property
        def babies(self) -> int:
            """Get the number of babies."""
            return int(self._by_field('party_size_babies'))
        
        @babies.setter
        def babies(self, value: int | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the number of babies.
            
            Parameters:
                value: Number of babies, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field('party_size_babies', value=value)
        
        @property
        def enquirySource(self) -> str:
            """Get the enquiry source (platform)."""
            try: 
                iCalImport = self.element(By.XPATH, '//i[contains(., "By: ICal")]').text
                for platform in PLATFORMS:
                    if platform in iCalImport: 
                        return platform
            except: 
                return 'Direct'

        @property
        def ownerBooking(self) -> bool:
            """Check if this is an owner booking."""
            return self.element(By.NAME, 'owner_booking').isChecked
        
        @ownerBooking.setter
        def ownerBooking(self, boolean: bool | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set whether this is an owner booking.
            
            Parameters:
                boolean: True if owner booking, None to keep current
                
            Returns:
                Self for method chaining
            """
            if self.ownerBooking:
                if not boolean: 
                    self.element(By.NAME, 'owner_booking').click(wait=1)
            else:
                if boolean: 
                    self.element(By.NAME, 'owner_booking').click(wait=1)
            return self

        @property
        def firstName(self) -> str:
            """Get the guest's first name."""
            return self._by_field('first_name')
        
        @firstName.setter
        def firstName(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the guest's first name.
            
            Parameters:
                value: First name, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field(name='first_name', value=value)

        @property
        def lastName(self) -> str:
            """Get the guest's last name."""
            return self._by_field('last_name')
        
        @lastName.setter
        def lastName(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the guest's last name.
            
            Parameters:
                value: Last name, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field(name='last_name', value=value)
                
        @property
        def email(self) -> str:
            """Get the guest's email address."""
            return self._by_field('email')
        
        @email.setter
        def email(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the guest's email address.
            
            Parameters:
                value: Email address, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field(name='email', value=value)
                
        @property
        def phone(self) -> str:
            """Get the guest's phone number."""
            return self._by_field('phone_2')
        
        @phone.setter
        def phone(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the guest's phone number.
            
            Parameters:
                value: Phone number, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field(name='phone_2', value=value)
                
        @property
        def extras(self) -> str:
            """Get the booking extras."""
            return self._by_field('custom_3')
        
        @extras.setter
        def extras(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the booking extras.
            
            Parameters:
                value: Extras text, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field(name='custom_3', value=value)

        @property
        def inboundFlight(self) -> str:
            """Get the inbound flight details."""
            return self._by_field('custom_1')
        
        @inboundFlight.setter
        def inboundFlight(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the inbound flight details.
            
            Parameters:
                value: Flight details, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field(name='custom_1', value=value)

        @property
        def outboundFlight(self) -> str:
            """Get the outbound flight details."""
            return self._by_field('custom_12')

        @outboundFlight.setter
        def outboundFlight(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the outbound flight details.
            
            Parameters:
                value: Flight details, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field(name='custom_12', value=value)

        @property
        def nifNumber(self) -> str:
            """Get the NIF tax number."""
            return self._by_field('custom_10')
        
        @nifNumber.setter
        def nifNumber(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the NIF tax number.
            
            Parameters:
                value: NIF number, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field(name='custom_10', value=value)
        

        @property
        def nationality(self) -> str:
            """Get the nationality."""
            return self._by_field('custom_13')
        
        @nationality.setter
        def nationality(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the nationality.
            
            Parameters:
                value: Nationality, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field(name='custom_13', value=value)
        

        @property
        def idCard(self) -> str:
            """Get the ID card number."""
            return self._by_field('custom_11')
        
        @idCard.setter
        def idCard(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the ID card number.
            
            Parameters:
                value: ID card number, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field(name='custom_11', value=value)
        
        @property
        def securityChargeMethod(self) -> str:
            """Get the security charge method."""
            return self._by_field('custom_14')
        
        @securityChargeMethod.setter
        def securityChargeMethod(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the security charge method.
            
            Parameters:
                value: Method text, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field(name='custom_14', value=value)
        
        @property
        def ownerClean(self) -> str:
            """Get the owner clean preference."""
            return self._by_field('custom_15')
        
        @ownerClean.setter
        def ownerClean(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the owner clean preference.
            
            Parameters:
                value: Clean preference, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field(name='custom_15', value=value)
        
        @property
        def ownerMeetGreet(self) -> str:
            """Get the owner meet & greet preference."""
            return self._by_field('custom_16')

        @ownerMeetGreet.setter
        def ownerMeetGreet(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the owner meet & greet preference.
            
            Parameters:
                value: Meet & greet preference, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_field(name='custom_16', value=value)

        @property
        def paymentMethod(self) -> str:
            """Get the payment method."""
            return self._by_selection('payment_method_guest')
        
        @paymentMethod.setter
        def paymentMethod(self, value: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the payment method.
            
            Parameters:
                value: Payment method, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._by_selection(name='payment_method_guest', value=value)

        @property
        def currency(self) -> str:
            """Get the currency code (EUR/GBP)."""
            value = self.element(By.NAME, 'currency_id').option
            if value == '2':
                return 'EUR'
            elif value == '1':
                return 'GBP'
            return value

        @currency.setter    
        def currency(self, which: str | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the currency.
            
            Parameters:
                which: Currency code ('EUR' or 'GBP'), or None to keep current
                
            Returns:
                Self for method chaining
            """
            if which == 'EUR': 
                value = '2'
            elif which == 'GBP': 
                value = '1'
            else:
                return self
            self.element(By.NAME, 'currency_id').selectByValue(value)
            return self
        
        @property
        def completedTasks(self) -> str:
            """Get the list of completed tasks."""
            return self.element(By.XPATH, '//fieldset[contains(., "Task history")]').text

        @property
        def basicRental(self) -> float:
            """Get the basic rental charge."""
            return float(self._by_field('basic_holiday_charge'))
        
        @basicRental.setter
        def basicRental(self, value: float | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the basic rental charge.
            
            Parameters:
                value: Amount to set, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._set_charge('basic_holiday_charge', value)

        @property
        def totalRental(self) -> float:
            """Get the total rental charge."""
            return float(self._by_field('total_holiday_charge'))
        
        @property
        def adminFee(self) -> float:
            """Get the administration fee."""
            return float(self._by_field('rental_supplements_charge'))
        
        @adminFee.setter
        def adminFee(self, value: float | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the administration fee.
            
            Parameters:
                value: Amount to set, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._set_charge('rental_supplements_charge', value)
        
        @property
        def securityCharge(self) -> float:
            """Get the security deposit amount."""
            return float(self._by_field('security_charge'))
        
        @securityCharge.setter
        def securityCharge(self, value: float | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set the security deposit amount.
            
            Parameters:
                value: Amount to set, or None to keep current
                
            Returns:
                Self for method chaining
            """
            return self._set_charge('security_charge', value)
        
        @property
        def myBookingForm(self) -> str:
            """Get the URL to the 'My Booking' form."""
            return self.element(By.XPATH, '//a[contains(., "My Booking form")]').attribute('href')

        @property
        def bookingDeposit(self) -> float:
            """Get the booking deposit amount."""
            value = self.elements(By.NAME, 'subtotal').attribute('value')[1]
            if isinstance(value, str):
                return string_to_float(value)
            return value
        
        def unlockGuestRegistrationForm(self, PIMSId) -> 'BrowsePIMS.OrderForms':
            """
            Unlock the guest registration form.
            
            Returns:
                Self for method chaining
            """
            super().goTo(f'{self._url}/confirmunblockguestreg.php?order_id={PIMSId}')
            self.element(By.XPATH, '//input[@value="Unlock now"]').click(wait=1.5)
            return self
        
        def newReminder(self, order_form_ID: str | int, reminder_name: str, 
                        month: int, day: int, year: int) -> 'BrowsePIMS.OrderForms':
            """
            Create a new reminder for a booking.
            
            Parameters:
                order_form_ID: ID of the order to add reminder to
                reminder_name: Description of the reminder
                month: Month number (1-12)
                day: Day of month
                year: Year (4 digits)
                
            Returns:
                Self for method chaining
            """
            self.GoTo(self.url + f'/orderform.php?order_id={order_form_ID}&formtype=reminderopen')
            self.element(By.NAME, 'reminder_description').input(reminder_name)
            self.element(By.XPATH, '//select[@id="reminder_due_date_Month_ID"]').selectByValue(f'{month - 1}')
            self.element(By.XPATH, '//select[@id="reminder_due_date_Day_ID"]').selectByVisibleText(f'{day}')
            self.element(By.XPATH, '//input[@id="reminder_due_date_Year_ID"]').clear().input(str(year), time=.1)
            self.element(By.XPATH, '//input[@value="Add reminder"]').click(wait=1.5)
            return self
        
        def newNote(self, note: str) -> 'BrowsePIMS.OrderForms':
            """
            Add a new note to the booking.
            
            Parameters:
                note: Text of the note to add
                
            Returns:
                Self for method chaining
            """
            self.frame('Blog').element(By.NAME, 'order_blog_text').input(note)    
            self.element(By.XPATH, "//input[@class='button']").click()
            return self.frame(default=True)
        
        def _by_field(self, name: str, value: str | datetime.date | None = None) -> str | Self:
            """
            Get or set a field value by name.
            
            Parameters:
                name: Field name
                value: Value to set, or None to just get current value
                
            Returns:
                Current value if getting, or self if setting
            """
            self.element(By.NAME, name)
            if value is None:
                return self.attribute('value').strip()
            self.clear().input(str(value), time=.1)
            return self
        
        def _by_selection(self, name: str, value: str | None = None) -> str | Self:
            """
            Get or set a selection field value by name.
            
            Parameters:
                name: Selection field name
                value: Value to select, or None to just get current value
                
            Returns:
                Current value if getting, or self if setting
            """
            self.element(By.NAME, name)
            if not value: 
                return self.option
            self.selectByVisibleText(str(value))
            return self

        def _set_charge(self, name: str, value: float | None = None) -> 'BrowsePIMS.OrderForms':
            """
            Set a charge field to a specific amount.
            
            Parameters:
                name: Field name
                value: Amount to set, or None to keep current
                
            Returns:
                Self for method chaining
            """
            if value is None:
                return self
            value = '{:.2f}'.format(value)
            self._by_field(name=name, value=value)
            if 'supplements' in name:
                type_ = 'rental_supplements'
            else:
                type_ = name
            if not self.element(By.NAME, type_ + '_fixed').isChecked:
                self.element(By.NAME, type_ + '_fixed').click(wait=1)
            return self
        
        def _convert_to_date(self, date: str | list[str]) -> datetime.date:
            """
            Convert date string or list to date object.
            
            Parameters:
                date: Datetime.date as string or list of strings
                
            Returns:
                Date object
            """
            if not isinstance(date, list): 
                date = date.split()
            if len(date) == 3: 
                day, month, year = date
            else: 
                weekday, day, month, year = date
            return dates.date(year, month, day)
        
        def __str__(self) -> str:
            """
            Get string representation of order form.
            
            Returns:
                Formatted string with all booking details
            """
            string = '\n\t\t_____ORDER FORM_____'
            string += f'\n\t\tProperty: {self.propertyName}'
            string += f'\n\t\tEnquiry Status: {self.enquiryStatus}'
            string += f'\n\t\tEnquiry Date: {self.enquiryDate}'
            string += f'\n\t\tArrival Date: {self.arrivalDate}'
            string += f'\n\t\tArrival Time: {self.arrivalTime}'
            string += f'\n\t\tDeparture Date: {self.departureDate}'
            string += f'\n\t\tDeparture Time: {self.departureTime}'
            string += f'\n\t\tAdults: {self.adults}'
            string += f'\n\t\tChildren: {self.children}'
            string += f'\n\t\tBabies: {self.babies}'
            string += f'\n\t\tEnquiry Source: {self.enquirySource}'
            string += f'\n\t\tOwner Booking: {self.ownerBooking}'
            string += f'\n\t\tFirst Name: {self.firstName}'
            string += f'\n\t\tLast Name: {self.lastName}'
            string += f'\n\t\tEmail: {self.email}'
            string += f'\n\t\tPhone: {self.phone}'
            string += f'\n\t\tExtras: {self.extras}'
            string += f'\n\t\tInbound Flight: {self.inboundFlight}'
            string += f'\n\t\tOutbound Flight: {self.outboundFlight}'
            string += f'\n\t\tNIF Number: {self.nifNumber}'
            string += f'\n\t\tSecurity Charge Method: {self.securityChargeMethod}'
            string += f'\n\t\tOwner Clean: {self.ownerClean}'
            string += f'\n\t\tOwner Meet Greet: {self.ownerMeetGreet}'
            string += f'\n\t\tPayment Method: {self.paymentMethod}'
            string += f'\n\t\tCurrency: {self.currency}'
            string += f'\n\t\tBasic Rental: {self.basicRental}'
            string += f'\n\t\tTotal Rental: {self.totalRental}'
            string += f'\n\t\tAdmin Fee: {self.adminFee}'
            string += f'\n\t\tSecurity Charge: {self.securityCharge}'
            string += f'\n\t\tBooking Deposit: {self.bookingDeposit}'
            return string
        
        def quit(self) -> None:
            """Close the browser session."""
            return self._driver.quit()