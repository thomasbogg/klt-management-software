from forms.arrival.responses import ArrivalFormResponses
from forms.arrival.vars import (
    GUEST_FIRST_NAME,
    GUEST_LAST_NAME,
    GUEST_EMAIL_ADDRESS,
    GUEST_PHONE_NUMBER,
    TOTAL_ADULTS,
    TOTAL_CHILDREN,
    TOTAL_BABIES,
    CLEAN_OPTION,
    IS_FOR_OWNER,
    MEET_GREET_OPTION,
    OWNER_COMMENTS,
)


class OwnerArrivalFormResponses(ArrivalFormResponses):
    
    def __init__(self, load: dict) -> None:
        """
        Initialize the OwnerArrivalFormResponses class.
        """
        super().__init__(load=load)
    
    @property
    def adults(self) -> int:
        """
        Get the number of adults from the form responses.
        # REQUIRED
        """
        return int(self._get(TOTAL_ADULTS))

    @property
    def children(self) -> int:
        """
        Get the number of children from the form responses.
        # NOT REQUIRED
        """
        value = self._get(TOTAL_CHILDREN)
        if value is None:
            return 0
        return int(value)

    @property
    def babies(self) -> int:
        """
        Get the number of babies from the form responses.
        # NOT REQUIRED
        """
        value = self._get(TOTAL_BABIES)
        if value is None:
            return 0
        return int(value)

    @property
    def clean(self) -> bool:
        """
        Determine if cleaning is required based on the form responses.
        """
        # REQUIRED
        # Form responses are:
        # 1. Yes, please!
        # 2. No, thank you.
        return '1. ' in self._get(CLEAN_OPTION)
    
    @property
    def selfBooking(self) -> bool:
        """
        Determine if the booking is self-booked based on the form responses.
        """
        # REQUIRED
        # Form responses are:
        # 1. Yes, this booking is for me!
        # 2. No, I have booked these dates for someone else.
        return '1. ' in self._get(IS_FOR_OWNER)

    @property
    def meetGreet(self) -> bool:
        """
        Determine if a meet and greet is required based on the form responses.
        """
        # Get answer first, then check if it is None
        # May be None as the section is skipped if self.selfBooking is True
        answer = self._get(MEET_GREET_OPTION)
        if answer is None:
            return False
        # Form responses are:
        # 1. Yes. I would like...
        # 2. No. The guests will...
        return '1. ' in answer

    @property
    def firstName(self) -> str:
        """
        Get the first name from the form responses.
        """
        name = self._get(GUEST_FIRST_NAME)
        if name:
            return name.split()[0]
        return ''

    @property
    def lastName(self) -> str:
        """
        Get the first name from the form responses.
        """
        name = self._get(GUEST_LAST_NAME)
        if name:
            return name.split()[-1]
        return ''

    @property    
    def phone(self) -> str:
        """
        Get the phone number from the form responses.
        """
        return self._get(GUEST_PHONE_NUMBER)

    @property
    def email(self) -> str:
        """
        Get the email from the form responses.
        """
        return self._get(GUEST_EMAIL_ADDRESS)
    
    @property
    def comments(self) -> str | None:
        """
        Get the comments from the form responses.
        """
        value = self._get(OWNER_COMMENTS)
        if value is None:
            return None
        return value.strip()

    def __str__(self):
        return super().__str__(
            [
                f'adults: {self.adults}',
                f'children: {self.children}',
                f'babies: {self.babies}',
                f'clean: {self.clean}',
                f'selfBooking: {self.selfBooking}',
                f'meetGreet: {self.meetGreet}',
                f'firstName: {self.firstName}',
                f'lastName: {self.lastName}',
                f'phone: {self.phone}',
                f'email: {self.email}',
                f'owner comments: {self.comments}',
            ]
        )