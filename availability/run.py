from default.database.functions import get_database, search_properties, set_property_location
from interfaces.interface import Interface
from interface.functions import get_location_criteria, get_int
from default.database.database import Database
from default.dates import dates
from datetime import date


def check_availability():
    """
    Check availability of properties in the database.
    This function retrieves the database and searches for properties that are available.
    """
    sections = Interface(title='THIS IS THE CHECK PROPERTY AVAILABILITY INTERFACE')

    location = get_location_criteria(sections)
    size = get_property_size(sections)
    guests = get_number_of_guests(sections)
    properties = get_properties(location, size, guests)

    start, end = get_dates(sections) 
    


def get_property_size(sections: Interface) -> dict[str, str | None]:
    """
    Get the size of a property.
    This function retrieves the size of a property based on its ID.
    """
    sections.section('Are we looking for a specific number of bedrooms?')
    size = sections.option(('1 bedroom', '2 bedrooms', '3 bedrooms', 'Unspecified'))
    if size == 4:
        return None
    return size


def get_number_of_guests(sections: Interface) -> int:
    """
    Get the number of guests.
    This function retrieves the number of guests based on user input.
    """
    sections.section('How many guests is this for?')
    return sections.integer()
    

def get_properties(location: dict, size: int, guests: int) -> list:
    """
    Search for available properties based on location and size.
    This function retrieves the database and searches for properties that match the criteria.
    """
    search = search_properties()
    set_property_location(search, location)
    
    if size:
        where = search.propertySpecs.where()
        where.bedrooms().isEqualTo(size)

    if guests:
        where = search.propertySpecs.where()
        where.maxGuests().isEqualTo(guests)
    
    return search.fetchall()


def get_dates(sections: Interface) -> tuple[date, date]:
    """
    Get the start and end dates for the booking.
    This function retrieves the start and end dates based on user input.
    """
    sections.section('What are the start and end dates?')
    subsections = sections.subsections()
    subsections.section('Start date')
    start = subsections.date()
    subsections.section('End date')
    end = subsections.date()
    if start > end:
        raise ValueError('Start date cannot be after end date.')
    if start == end:
        raise ValueError('Start date cannot be the same as end date.')
    if start < dates.date():
        raise ValueError('Start date cannot be in the past.')
    if end < dates.date():
        raise ValueError('End date cannot be in the past.')
    return start, end


def get_only_empty():
    pass
