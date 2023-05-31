from dash import dash, html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import re
import pandas as pd
from datetime import datetime, timedelta
import base64
import json

# Open the file in read mode
with open('JUN23_JFK_320_PILOTS.txt', 'r') as file:
    file_contents = file.read()

table_columns = ['p_code', 'checkin', 'checkout', 'credit_sum', 'n_days', 'block_sum', 'softtime','tafb','flight_data']
display_columns = ['Code','Check-In','Check-out','Credit','Days','Block','Soft','TAFB','Flight Data']

flight_columns = ['Day', 'Flt', 'Dep', 'D.Local', 'Arr', 'A.Local', 'Turn', 'Eqp', 'Block']

def format_timedelta(td):
    total_hours = td.total_seconds() // 3600
    hours = int(total_hours)  # Hours within a day
    minutes = int((td.total_seconds() // 60) % 60)  # Minutes
    return f"{hours:03d}:{minutes:02d}"

def format_timedelta_alt(td):
    days = td.days
    hours = td.seconds // 3600
    minutes = (td.seconds // 60) % 60
    return f"{days} days, {hours:02d}:{minutes:02d}"

pairings = file_contents.split('----------------------------------------------------------------------------------------------------')
del pairings[0]
del pairings[-1]

table_data = pd.DataFrame(columns=table_columns)

for pairing in pairings:

    flight_data = []
    obs = pd.DataFrame(columns=table_columns)
    flight_table = pd.DataFrame(columns=flight_columns)
    p_code = ""
    n_days = 0
    credit_sum = timedelta()
    block_sum = timedelta()
    softtime = timedelta()
    tafb = timedelta()
    my = datetime.now()  # Or an appropriate default value
    d = []
    checkins = []
    checkouts = []   
    
    flight_data = re.findall(r'(\d)?(?:\s+|\s+[A-Z]{2}\s+)(\w+)\s+(\w{3})\s+(\d{2}:\d{2})\s+(\w{3})\s+(\d{2}:\d{2})\s*(\d{3}:\d{2})?\s*(\w*)?\s+(\d{3}:\d{2})', pairing)

    # Extract other variables of interest

    ## From the top line pull the pairing code and the number of days of the pairing

    p_code = re.findall(r'J\d{1,2}[A-Z]?\d{2}', pairing)
    p_code = p_code[0]

    n_days = re.findall(r'(\d+)-Day', pairing)
    n_days = int(n_days[0])

    ## Near the bottom pull both the total credit and sum of the block times and use it to calculate the soft time. Plus record time away from base

    credit_sum = re.findall(r'Credit:\s(\d{3}:\d{2})', pairing)
    credit_sum = credit_sum[0]
    hours, minutes = map(int, credit_sum.split(':'))
    credit_sum = timedelta(hours=hours, minutes=minutes)

    block_sum = re.findall(r'\w\s{40}(\d{3}:\d{2})', pairing)
    block_sum = block_sum[0]
    hours, minutes = map(int, block_sum.split(':'))
    block_sum = timedelta(hours=hours, minutes=minutes)

    softtime = credit_sum - block_sum

    tafb = re.findall(r'TAFB:\s(\d{3}:\d{2})', pairing)
    tafb = tafb[0]
    hours, minutes = map(int, tafb.split(':'))
    tafb = timedelta(hours=hours, minutes=minutes)

    credit_sum = format_timedelta(credit_sum)
    block_sum = format_timedelta(block_sum)
    softtime = format_timedelta(softtime)
    tafb = format_timedelta_alt(tafb)

    ## Here, we concern ourselves with dates. We want the dates in the calendar on the right to match with the month and year above the calendar.

    my = re.findall(r'[A-Z]{3}\s\d{4}', pairing)
    my = datetime.strptime(my[0],"%b %Y")

    d = list()
    d_list = re.findall(r'\|(\d{2})\s|\s(\d{2})\s', pairing)

    d = [int(num) for tup in d_list for num in tup if num]
    mdy = [my + timedelta(days=item-1) for item in d]

    ## Further, we want check in and checkout times to be associated with these dates.

    checkin = re.findall(r'Check-In\s(\d{2}:\d{2})', pairing)
    checkin = datetime.strptime(checkin[0], "%H:%M")
    checkins = []
    for checkin_date in mdy:
        checkin_datetime = datetime.combine(checkin_date.date(), checkin.time())
        checkins.append(checkin_datetime)

    checkout = re.findall(r'Check-Out\s(\d{2}:\d{2})', pairing)
    checkout = datetime.strptime(checkout[0], "%H:%M")
    checkouts = []
    for checkout_date in mdy:
        checkout_datetime = datetime.combine(checkout_date.date(), checkout.time()) + timedelta(days=n_days - 1)
        checkouts.append(checkout_datetime)

    ## Now all that remains is to make our table_data with all pairings. But because we want to filter by dates, we actually make an observation for each date a pairing is offered as well.

    checkinouts = []
    for item1, item2 in zip(checkins, checkouts):
        checkinouts.append((item1, item2))

    for checkinout in checkinouts:
        checkin, checkout = checkinout
        obs = pd.DataFrame([[p_code, checkin, checkout, credit_sum, n_days, block_sum, softtime, tafb, flight_data]], columns = table_columns)
        table_data = pd.concat([table_data, obs], ignore_index=True)

    table_data['flight_data'] = table_data['flight_data'].astype(str)

    table_data.to_json('default_data.json', orient='records')
