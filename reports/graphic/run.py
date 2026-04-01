import matplotlib.pyplot as plt
from reports.graphic.fetch import FetchGuestArrivals, FetchOwnerArrivals, FetchGuestEnquiries
from accountancy.load import AccountancyBooking
from accountancy.internal.commissions.load import CommissionsBooking
from default.dates import dates
from default.settings import LOCAL_STORAGE_DIR


def produce_end_of_month_graph_reports(month=None, year=None, property=None):

    if property : property_spec = f' for {property}'
    
    else : property_spec = ''

    graphs = {

        f'Cumulative Converted Enquiries by Year{property_spec}' : {
            
            'x': 'Month of First Enquiry', 
       
            'y': 'Total Valid Enquiries'
        
        },
        
        f'Cumulative Guest Nights Booked by Year{property_spec}' : {
            
            'x': 'Month of First Enquiry', 
        
            'y': 'Total Nights'
        
        },
        
        f'Cumulative Owner Nights Booked by Year{property_spec}' : {
            
            'x': 'Month of First Enquiry', 
        
            'y': 'Total Nights'
        
        },
        
        f'Cumulative Guest Arrivals by Year{property_spec}' : {
            
            'x': 'Month of Arrival', 
        
            'y': 'Total Arrivals'
        
        },
        
        f'Cumulative Owner Arrivals by Year{property_spec}' : {
            
            'x': 'Month of Arrival', 
        
            'y': 'Total Arrivals'
        
        },
        
        f'Cumulative Guest Nights Stayed by Year{property_spec}' : {
            
            'x': 'Month of Arrival', 
        
            'y': 'Total Nights'
        
        },
        
        f'Cumulative Owner Nights Stayed by Year{property_spec}' : {
            
            'x': 'Month of Arrival', 
        
            'y': 'Total Nights'
        
        },
        
        f'Cumulative Rental Revenue by Year{property_spec}' : {
            
            'x': 'Revenue Month', 
        
            'y': 'Total Revenue (€)'
            
        },
        
        f'Cumulative Payouts to Owner by Year{property_spec}': {
            
            'x': 'Payment Month', 
        
            'y': 'Total Paid (€)'
        
        },
        
        f'Cumulative Commission Earned by Year (Us){property_spec}': {
            
            'x': 'Commission Month', 
        
            'y': 'Total Commission (Us)'
        
        },
    }

    filenames = list()

    for title, axes in graphs.items():
       
        fig, ax = plt.subplots()
       
        ax.set_title(title)
       
        ax.set_xlabel(axes['x'])
       
        ax.set_ylabel(axes['y'])

        ordered = dict()

        for y in range(2023, year + 1) : ordered[y] = {i: (0 if i <= month or y < year else None) for i in range(1, 13)}

        owner_in_title = 'Owner' in title

        start, end = dates.date(year=2023, month=1, day=1), dates.lastOfMonth(-1)

        if 'Enquiries' in title : set_enquiries_data(start=start, end=end, ordered=ordered, property=property)

        elif 'Nights Booked' in title:
            
            if owner_in_title : end = dates.date(year=year, month=12, day=31)
            
            set_nights_booked_data(start=start, end=end, ordered=ordered, property=property, owner=owner_in_title)

        elif 'Arrivals' in title : set_arrivals_data(start=start, end=end, ordered=ordered, property=property, owner=owner_in_title)

        elif 'Nights Stayed' in title : set_nights_stayed_data(start=start, end=end, ordered=ordered, property=property, owner=owner_in_title)

        elif 'Revenue' in title : set_revenue_data(start=start, end=end, ordered=ordered, property=property)

        elif 'Payouts' in title : set_payout_data(start=start, end=end, ordered=ordered, property=property)

        elif 'Commission' in title and not property : set_commission_data(start=start, end=end, ordered=ordered, property=property)

        else : continue

        if 'Commission' in title and property : continue
        
        legends = list()
        
        for y, months in ordered.items():
            
            legends.append(f'{y}')
           
            values = list(months.values())
            
            for i in range(1, len(values)):
                
                if values[i] is not None : values[i] += values[i - 1]

            ax.plot(list(months.keys()), values)
        
        ax.legend(legends)

        filename = f'{LOCAL_STORAGE_DIR}/reports/{title}.png'

        plt.savefig(filename)

        filenames.append(filename)

        #plt.show()
    
    return filenames


def set_enquiries_data(start, end, ordered, property=None):

    fetched = FetchGuestEnquiries(start=start, end=end, property=property).Get()

    for loaded in fetched:
    
        booking = AccountancyBooking(loaded)

        date = booking.stay.enquiry_date()

        if not date : continue
        
        year, month = date.year, date.month

        if not ordered[year][month] : ordered[year][month] = 0

        ordered[year][month] += 1

    return None


def set_nights_booked_data(start, end, ordered, property=None, owner=None):

    if not owner : fetched = FetchGuestEnquiries(start=start, end=end, property=property).Get()
    
    else : fetched = FetchOwnerArrivals(start=start, end=end, property=property).Get()
    
    for loaded in fetched:
        
        booking = AccountancyBooking(loaded)

        nights = booking.stay.total_nights()
        
        enquiry_date = booking.stay.enquiry_date()
        
        arrival_date = booking.stay.arrival_date()

        if not arrival_date or not enquiry_date or arrival_date.year not in ordered.keys() : continue
        
        if enquiry_date.year != arrival_date.year : year, month = arrival_date.year, 1

        else : year, month = enquiry_date.year, enquiry_date.month

        if not ordered[year][month] : ordered[year][month] = 0

        ordered[year][month] += nights

    return None


def set_arrivals_data(start, end, ordered, property=None, owner=None):

    if not owner:
        fetched = FetchGuestArrivals(start=start, end=end, property=property).Get()
    else:
        fetched = FetchOwnerArrivals(start=start, end=end, property=property).Get()

    for loaded in fetched:
        booking = AccountancyBooking(loaded)

        date = booking.stay.arrival_date()

        if not date:
            continue
        
        month = date.month
        year = date.year

        if not ordered[year][month]:
            ordered[year][month] = 0

        ordered[year][month] += 1


def set_nights_stayed_data(start, end, ordered, property=None, owner=None):

    if not owner:
        fetched = FetchGuestArrivals(start=start, end=end, property=property).Get()
    else:
        fetched = FetchOwnerArrivals(start=start, end=end, property=property).Get()

    for loaded in fetched:
        booking = AccountancyBooking(loaded)

        nights = booking.stay.total_nights()
        date = booking.stay.arrival_date()

        if not date:
            continue
        
        month = date.month
        year = date.year

        if not ordered[year][month]:
            ordered[year][month] = 0

        ordered[year][month] += nights


def set_revenue_data(start, end, ordered, property=None):
   
    fetched = FetchGuestArrivals(start=start, end=end, property=property).Get()

    for loaded in fetched:
        booking = AccountancyBooking(loaded)

        total = booking.charges.basic_rental()
        month = booking.stay.arrival_date().month
        year = booking.stay.arrival_date().year

        if not total:
            continue

        if not ordered[year][month]:
            ordered[year][month] = 0
        
        ordered[year][month] += total


def set_payout_data(start, end, ordered, property=None):
   
    fetched = FetchGuestArrivals(start=start, end=end, property=property).Get()

    for loaded in fetched:
        booking = AccountancyBooking(loaded)

        total = booking.charges.payment_to_owner()
        month = booking.stay.arrival_date().month
        year = booking.stay.arrival_date().year

        if not total:
            continue

        if not ordered[year][month]:
            ordered[year][month] = 0
        
        ordered[year][month] += total


def set_commission_data(start, end, ordered, property=None):

    fetched = FetchGuestArrivals(start=start, end=end, property=property).Get()

    for loaded in fetched:
        booking = CommissionsBooking(loaded)

        total = booking.charges.klt_commission()
        month = booking.stay.arrival_date().month
        year = booking.stay.arrival_date().year

        if not total:
            continue

        if not ordered[year][month]:
            ordered[year][month] = 0
        
        ordered[year][month] += total