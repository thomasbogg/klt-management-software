import datetime
import re

from apis.google.forms.form import GoogleForm
from default.dates import dates

from forms.arrival.vars import (
    ARRIVAL_METHOD,
    INBOUND_FLIGHT_NUMBER,
    INBOUND_FLIGHT_TIME,
    OUTBOUND_FLIGHT_NUMBER,
    OUTBOUND_FLIGHT_TIME,
    CAR_HIRE,
    ARRIVAL_TIME,
    ARRIVAL_COMMENTS,
    AIRPORT_TRANSFER_OPTION,
    CHILD_SEATS,
    EXCESS_BAGGAGE,
    WELCOME_PACK_OPTION,
    MID_STAY_CLEAN_OPTION,
    COT_OPTION,
    HIGHCHAIR_OPTION,
)


class ArrivalFormResponses(GoogleForm.Responses):

    def __init__(self, load: dict | None = None) -> None:
        """
        Initialize the ArrivalFormResponses class.
        """
        super().__init__(load=load)
    
    @property
    def arrival(self) -> str|None:
        """
        Get the arrival information from the form responses.
        """
        # Form responses are:
        # 1. Flight to FARO airport
        # 2. Flight to LISBON airport
        # 3. Bus to Albufeira station
        # 4. Train to Ferreiras (Albufeira) station
        # 5. Driving from another location
        # 6. Other
        return self._get(ARRIVAL_METHOD)
    
    @property
    def arrivalIsFlight(self) -> bool:
        """
        Check if the arrival method is a flight.
        """
        return '1. ' in self.arrival or '2. ' in self.arrival

    @property
    def flightIsFaro(self) -> bool:
        """
        Check if the flight is to Faro airport.
        """
        return '1. ' in self.arrival    

    @property
    def inboundFlightNumber(self) -> str | None:
        """
        Get the inbound flight number from the form responses.
        """
        value = self._get(INBOUND_FLIGHT_NUMBER)
        if not value:
            return None
        return value.strip().upper()
    
    @property
    def inboundFlightTime(self) -> datetime.time | None:
        """
        Get the inbound flight time from the form responses.
        """
        value = self._get(INBOUND_FLIGHT_TIME)
        if not value:
            return None
        return dates.convertToTime(value)

    @property
    def outboundFlightNumber(self) -> str | None:
        """
        Get the outbound flight number from the form responses.
        """
        value = self._get(OUTBOUND_FLIGHT_NUMBER)
        if not value:
            return None
        return value.strip().upper()
    
    @property
    def outboundFlightTime(self) -> datetime.time | None:
        """
        Get the outbound flight time from the form responses.
        """
        value = self._get(OUTBOUND_FLIGHT_TIME)
        if not value:
            return None
        return dates.convertToTime(value)

    @property
    def carHire(self) -> bool:
        """
        Check if car hire is required based on the form responses.
        """
        # Form responses are:
        # 1. Yes
        # 2. No
        value = self._get(CAR_HIRE)
        if value is None:
            return None
        return '1. ' in value or 'Yes' in value

    @property
    def arrivalTime(self) -> datetime.time | None:
        """
        Get the bus arrival time from the form responses.
        """
        value = self._get(ARRIVAL_TIME)
        if not value:
            return None
        return dates.convertToTime(value)

    @property
    def arrivalComments(self) -> str | None:
        """
        Get the driving arrival comments from the form responses.
        """
        value = self._get(ARRIVAL_COMMENTS)
        if not value:
            return None
        return value.strip()[:45]
    
    @property
    def airportTransfers(self) -> str | None:
        """
        Get the airport transfers information from the form responses.
        """
        # Form responses are:
        # 1. Inbound and Outbound
        # 2. Inbound Only
        # 3. Outbound Only
        # 4. None
        value = self._get(AIRPORT_TRANSFER_OPTION)
        if value is None:
            return False
        return '1. ' in value
    
    @property
    def airportTransferInboundOnly(self) -> bool:
        """
        Check if the airport transfer is inbound only based on the form responses.
        """
        value = self._get(AIRPORT_TRANSFER_OPTION)
        if value is None:
            return False
        return '2. ' in value

    @property
    def airportTransferOutboundOnly(self) -> bool:
        """
        Check if the airport transfer is outbound only based on the form responses.
        """
        value = self._get(AIRPORT_TRANSFER_OPTION)
        if value is None:
            return False
        return '3. ' in value

    @property
    def childSeats(self) -> str | None:
        """
        Get the child seats information from the form responses.
        """
        return self._parse_child_seats(self._get(CHILD_SEATS))

    @property
    def excessBaggage(self) -> str | None:
        """
        Get the excess baggage information from the form responses.
        """
        return self._get(EXCESS_BAGGAGE)

    @property
    def welcomePack(self) -> bool:
        """
        Check if a welcome pack is included based on the form responses.
        """
        # Form response is tickbox 'Yes, please!': will be None is not selected
        return bool(self._get(WELCOME_PACK_OPTION))

    @property
    def midStayClean(self) -> bool:
        """
        Check if mid-stay cleaning is required based on the form responses.
        """
        # Form response is tickbox 'Yes, please!': will be None is not selected
        return bool(self._get(MID_STAY_CLEAN_OPTION))

    @property
    def cot(self) -> bool:
        """
        Check if a cot is required based on the form responses.
        """
        # Form response is tickbox 'Yes, please!': will be None is not selected
        return bool(self._get(COT_OPTION))

    @property
    def highChair(self) -> bool:
        """
        Check if a high chair is required based on the form responses.
        """
        # Form response is tickbox 'Yes, please!': will be None is not selected
        return bool(self._get(HIGHCHAIR_OPTION))

    def _parse_child_seats(self, string: str) -> str | None:
        """
        Parses child seat requirements from a string input.
        
        This function extracts age information from a comma-separated string
        and formats it appropriately, distinguishing between months and years.
        
        Args:
            string (str): A comma-separated string containing child ages.
        
        Returns:
            str | None: A formatted string of child ages or None if no valid
                ages are found.
        """
        if not string: 
            return None
    
        result: list[str] = []
        ages: list[str] = string.split(',')

        for age in ages:
            age = age.strip()
            search: re.Match[str] | None = re.search(r'([0-9]+)', age)
            if not search:
                continue
            
            ageNumber: str = search.group(1)
            if 'month' in age.lower():
                ageNumber += ' month(s)'
            result.append(ageNumber)
        
        return ','.join(result)

    def __str__(self, details=list()):
        details += [
            f'arrival: {self.arrival}',
            f'arrivalIsFlight: {self.arrivalIsFlight}',
            f'flightIsFaro: {self.flightIsFaro}',
            f'inboundFlightNumber: {self.inboundFlightNumber}',
            f'inboundFlightTime: {self.inboundFlightTime}',
            f'outboundFlightNumber: {self.outboundFlightNumber}',
            f'outboundFlightTime: {self.outboundFlightTime}',
            f'carHire: {self.carHire}',
            f'arrivalTime: {self.arrivalTime}',
            f'arrivalComments: {self.arrivalComments}',
            f'airportTransfers: {self.airportTransfers}',
            f'airportTransferInboundOnly: {self.airportTransferInboundOnly}',
            f'airportTransferOutboundOnly: {self.airportTransferOutboundOnly}',
            f'childSeats: {self.childSeats}',
            f'excessBaggage: {self.excessBaggage}',
            f'welcomePack: {self.welcomePack}',
            f'midStayClean: {self.midStayClean}',
            f'cot: {self.cot}',
            f'highChair: {self.highChair}',
        ]
        return f'\n\t\t{"\n\t\t".join(details)}'