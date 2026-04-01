import datetime

from default.dates import dates


class updatedates(dates):
    """
    A class for calculating date ranges used in various update operations.
    
    This class extends the Dates class to provide specialized methods for
    determining appropriate date ranges for different types of updates
    in the KLT application.
    """

    def __init__(self) -> None:
        """Initialize updatedates instance."""
        super().__init__()

    @classmethod
    def isForYesterday(cls) -> bool:
        """
        Determine if updates should use yesterday's date based on current hour.
        
        Returns:
            True if current hour is before 11AM, indicating we should use yesterday's date.
        """
        return cls.hour() < 11

    @classmethod
    def calculate(cls, days: int = 0, months: int = 0) -> datetime.date:
        """
        Calculate a date relative to today, adjusting for early morning updates.
        
        Args:
            days: Number of days to add/subtract from reference date.
            months: Number of months to add/subtract from reference date.
            
        Returns:
            A calculated date object.
        """
        if cls.isForYesterday(): 
            days -= 1 
        return super().calculate(date=super().date(), days=days, months=months)

    @classmethod
    def date(cls) -> datetime.date:
        """
        Get today's date or yesterday's date depending on current time.
        
        Returns:
            The appropriate reference date for updates.
        """
        if cls.isForYesterday(): 
            return super().date()
        return cls.calculate()
    
    @classmethod
    def day(cls) -> int:
        """
        Get the day of the month for the appropriate reference date.
        
        Returns:
            The day number (1-31) of the reference date.
        """
        return cls.date().day

    # Helper methods for common date calculations
    
    def monthly_update_dates(self, month: int = 0) -> tuple[datetime.date, datetime.date]:
        """
        Calculate the date range for monthly updates.
        
        If current day is before the 5th, use previous month.
        
        Args:
            month: Month offset from current month.
            
        Returns:
            A tuple containing the first and last day of the target month.
        """
        if self.day() < 5: 
            month = -1
        return self.firstOfMonth(month), self.lastOfMonth(month)  

    @classmethod
    def _is_low_season(cls) -> bool:
        """
        Determine if the current date is in the low season.
        
        Low season is defined as September 16th through March 31st.
        
        Returns:
            True if current date is in low season, False otherwise.
        """
        if cls.month() > 9 and cls.day() > 15:
            return True
        if cls.month() < 4: 
            return True
        return False

    # Date ranges for various update operations
    
    @classmethod
    def ABA_sheets_update_arrival_dates(cls) -> list[datetime.date]:
        """
        Get a list of dates for ABA sheet updates.
        
        Returns a list of dates at various intervals from today (0, 1, 3, 7, 15, 31 days),
        with additional future dates (62, 93 days) during low season.
        
        Returns:
            A list of dates for ABA sheet updates.
        """
        daysTime = [0, 1, 3, 7, 15, 31]
        if cls._is_low_season(): 
            daysTime += [62, 93]
        return [cls.calculate(days=day) for day in daysTime]
    
    @classmethod
    def is_Sunday(cls) -> bool:
        """
        Check if today is a Sunday.
        
        Returns:
            True if today is Sunday, False otherwise.
        """
        return cls.date().weekday() == 6

    @classmethod
    def ABA_sheets_update_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for ABA sheets updates.
        
        Returns:
            A tuple containing start and end dates for ABA sheet updates.
        """
        if cls._is_low_season(): 
            return cls.calculate(days=-60), cls.calculate(days=90)
        return cls.calculate(days=-10), cls.calculate(days=30)

    @classmethod
    def airport_transfers_request_emails_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for airport transfer request emails.
        
        Returns:
            A tuple containing start and end dates for airport transfer emails.
        """
        return cls.calculate(days=1), cls.calculate(days=17)

    @classmethod
    def arrival_details_prompting_emails_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for prompting guests for arrival details.
        
        Returns:
            A tuple containing start and end dates for arrival details emails.
        """
        return cls.calculate(days=1), cls.calculate(days=6)

    @classmethod
    def arrival_forms_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for arrival forms processing.
        
        Returns:
            A tuple containing start and end dates for arrival forms.
        """
        return cls.calculate(days=1), cls.calculate(days=28)

    @classmethod
    def arrival_information_emails_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for sending arrival information emails.
        
        Returns:
            A tuple containing start and end dates for arrival information emails.
        """
        return cls.calculate(days=3), cls.calculate(days=15)

    @classmethod
    def balance_payment_emails_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for balance payment reminder emails.
        
        Returns:
            A tuple containing start and end dates for balance payment emails.
        """
        return cls.calculate(days=57), cls.calculate(days=63)
    
    @classmethod
    def bookingCom_guest_contacts_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for processing Booking.com guest contacts.
        
        Returns:
            A tuple containing start and end dates for guest contact processing.
        """
        return cls.calculate(days=2), cls.calculate(days=35)

    @classmethod
    def bookingCom_update_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for Booking.com updates.
        
        Returns:
            A tuple containing start and end dates for Booking.com updates.
        """
        return cls.calculate(), cls.calculate(days=350)

    @classmethod
    def calendar_update_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for calendar updates.
        
        Returns:
            A tuple containing start and end dates for calendar updates.
        """
        return cls.calculate(days=1), cls.calculate(days=17)

    @classmethod
    def check_in_information_emails_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for sending check-in information emails.
        
        Returns:
            A tuple containing start and end dates for check-in information emails.
        """
        return cls.calculate(days=1), cls.calculate(days=2)

    @classmethod
    def commissions_update_dates(cls, month: int = 0) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for commission updates.
        
        Args:
            month: Month offset from current month.
            
        Returns:
            A tuple containing start and end dates for commission updates.
        """
        return cls.monthly_update_dates(cls, month)

    @classmethod
    def delete_backups_dates(cls) -> datetime.date:
        """
        Get start date for backup deletion operations.
        
        Returns:
            The first day of the previous month.
        """
        return cls.firstOfMonth(-1)

    @classmethod
    def delete_old_arrival_forms_date(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for deleting old arrival forms.
        
        Returns:
            The cut-off date for deleting old arrival forms.
        """
        return cls.calculate(-15)

    @classmethod
    def edgered_update_dates(cls, month: int = 0) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for Edgered updates.
        
        Args:
            month: Month offset from current month.
            
        Returns:
            A tuple containing start and end dates for Edgered updates.
        """
        return cls.monthly_update_dates(cls, month)

    @classmethod
    def calculate_mon_owners_totals_update_dates(cls, month: int = 0) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for Edgered updates.
        
        Args:
            month: Month offset from current month.
            
        Returns:
            A tuple containing start and end dates for Edgered updates.
        """
        if cls.day() <= 25: 
            month = -1
        return cls.firstOfMonth(month - 2), cls.lastOfMonth(month)

    @classmethod
    def final_day_reminder_emails_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for sending final day reminder emails.
        
        Returns:
            A tuple containing start and end dates for final day reminder emails.
        """
        return cls.calculate(days=1), cls.calculate(days=2)

    @classmethod
    def four_weeks_emails_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for four-week reminder emails.
        
        Returns:
            A tuple containing start and end dates for four-week reminder emails.
        """
        return cls.calculate(days=1), cls.calculate(days=28)

    @classmethod
    def gen_acc_update_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for general accounting updates.
        
        Returns:
            A tuple containing first and last day of the previous month.
        """
        return cls.firstOfMonth(-1), cls.lastOfMonth(-1)

    @classmethod
    def goodbye_emails_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for sending goodbye emails to departing guests.
        
        Returns:
            A tuple containing start and end dates for goodbye emails.
        """
        return cls.calculate(days=-6), cls.calculate(days=-4)

    @classmethod
    def guest_registration_emails_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for guest registration emails.
        
        Returns:
            A tuple containing start and end dates for guest registration emails.
        """
        return cls.calculate(), cls.calculate(days=5)

    @classmethod
    def guest_registrations_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for processing guest registrations.
        
        Returns:
            A tuple containing start (7 days ago) and end dates (today).
        """
        return cls.calculate(days=-7), cls.calculate(days=3)

    @classmethod
    def harmonious_jungle_update_dates(cls, month: int = 0) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for Harmonious Jungle updates.
        
        Args:
            month: Month offset from current month.
            
        Returns:
            A tuple containing start and end dates for Harmonious Jungle updates.
        """
        return cls.monthly_update_dates(cls, month)

    @classmethod
    def internal_accountant_update_dates(cls, year: int = 0) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for internal accountant updates.
        
        Args:
            year: Year offset from current year.
            
        Returns:
            A tuple containing the first and last day of the specified year.
        """
        return cls.date(year=cls.year() - year - 1, month=11, day=1), cls.lastOfYear(year)

    @classmethod
    def internal_reports_update_dates(cls, value: int = 0) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for internal reports updates.
        
        Args:
            value: Year offset for end date. Start date will be one year earlier.
            
        Returns:
            A tuple containing start and end dates spanning two years.
        """
        return cls.firstOfYear(value - 1), cls.lastOfYear(value + 1)

    @classmethod
    def KKLJ_sheets_update_dates(cls) -> datetime.date:
        """
        Get reference date for KKLJ sheet updates.
        
        Returns:
            A date 10 days before the reference date.
        """
        return cls.calculate(days=-31)

    @classmethod
    def management_arrivals_emails_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for management arrival emails.
        
        Returns:
            A tuple containing start and end dates for management arrival emails.
        """
        return cls.calculate(days=1), cls.calculate(days=17)

    @classmethod
    def management_cleans_emails_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for management cleaning emails.
        
        Returns:
            A tuple containing start and end dates for management cleaning emails.
        """
        return cls.calculate(days=1), cls.calculate(days=17)

    @classmethod
    def management_updates_emails_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for management update emails.
        
        Returns:
            A tuple containing start and end dates for management update emails.
        """
        return cls.calculate(days=-2), cls.calculate(days=1)

    @classmethod
    def guestPromptDates(cls) -> list[datetime.date]:
        """
        Get dates for sending guest prompts.
        
        Returns:
            A list of dates when guests should be prompted (14 and 7 days ahead).
        """
        return [cls.calculate(days=14), cls.calculate(days=7)]

    @classmethod
    def owner_prompting_dates(cls) -> tuple[datetime.date, datetime.date, datetime.date, datetime.date]:
        """
        Get dates for prompting property owners at different intervals.
        
        Returns:
            A tuple containing four dates at 1, 2, 4, and 6 days from reference date.
        """
        return (
            cls.calculate(days=1),
            cls.calculate(days=2),
            cls.calculate(days=4),
            cls.calculate(days=6)
        )

    @classmethod
    def owner_reports_update_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for owner reports updates.
        
        Returns:
            A tuple containing start (first day of current year) and end 
            (last day of next year) dates.
        """
        return cls.firstOfYear(), cls.lastOfYear(1)

    @classmethod
    def payments_to_owner_update_dates(cls, month: int = 0) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for payments to owner updates.
        
        If current day is on or before the 15th, use the previous month.
        
        Args:
            month: Month offset from determined month.
            
        Returns:
            A tuple containing start and end dates spanning two months.
        """
        if cls.month() == 1 and 6 <= cls.day() <= 15:
            return cls.firstOfMonth(0), cls.lastOfMonth(0)
        
        if cls.day() <= 15: month -= 1
        return cls.firstOfMonth(month), cls.lastOfMonth(month + 1)

    @classmethod
    def payments_to_owners_email_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for payments to owners emails.
        
        Returns:
            A tuple containing start (7 days ago) and end (yesterday) dates.
        """
        return cls.calculate(days=-7), cls.calculate(days=-1)

    @classmethod
    def PIMS_platform_update_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for PIMS platform updates.
        
        Returns:
            A tuple containing start (10 days ago) and end (400 days from now) dates.
        """
        return cls.calculate(days=-10), cls.calculate(days=400)

    @classmethod
    def PIMS_update_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for PIMS updates.
        
        Returns:
            A tuple containing start (150 days ago) and end (365 days from now) dates.
        """
        return cls.calculate(days=-150), cls.calculate(days=665)

    @classmethod
    def ptag_update_dates(cls, year: int = 0) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for PTAG updates.
        
        Args:
            year: Year offset from current year.
            
        Returns:
            A tuple containing the first and last day of the specified year.
        """
        return cls.firstOfYear(year), cls.lastOfYear(year)

    @classmethod
    def realco_email_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for Realco emails.
        
        Returns:
            A tuple containing start (first of next month) and end (last of next month) dates.
        """
        return cls.firstOfMonth(1), cls.lastOfMonth(1)

    @classmethod
    def security_deposit_request_emails_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for security deposit request emails.
        
        Returns:
            A tuple containing start and end dates for security deposit request emails.
        """
        return cls.calculate(days=3), cls.calculate(days=21)

    @classmethod
    def security_deposit_returns_email_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for security deposit return emails.
        
        Returns:
            A tuple containing start (8 days ago) and end (2 days ago) dates.
        """
        return cls.calculate(days=-8), cls.calculate(days=-2)

    @classmethod
    def review_airbnb_guests_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for reviewing Airbnb guests.
        
        Returns:
            A tuple containing start (today) and end (31 days from now) dates.
        """
        return cls.calculate(days=-10), cls.calculate(days=-2)
    
    @classmethod
    def complete_empty_guest_details_dates(cls) -> tuple[datetime.date, datetime.date]:
        """
        Get date range for completing empty guest details.
        
        Returns:
            A tuple containing start (30 days ago) and end (today) dates.
        """
        return cls.calculate(-30), cls.calculate(-1)