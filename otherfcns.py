pairings = file_contents.split('----------------------------------------------------------------------------------------------------\n')
del pairings[0]
del pairings[-1]
#pairings_list = list()

for pairing in pairings:
    
    flight_data = re.findall(r'(\d)?\s+(\d+)\s+(\w{3})\s{2}(\d{2}:\d{2})\s{3}(\w{3})\s{2}(\d{2}:\d{2})\s*(\d{3}:\d{2})?\s*(\w{3})\s{3}(\d{3}:\d{2})', pairing) # raw data is a simple dataset stored in confidential.py
    flight_table = pd.DataFrame(flight_data, columns=flight_columns)

    # Extract other variables of interest

    ## From the top line pull the pairing code and the number of days of the pairing

    p_code = re.findall(r'[A-Z]\d+', pairing)
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
    d_lines = re.findall(r'\|.*\|', pairing)
    for week in d_lines:
        d_strs = re.findall(r'\d+', week)
        for d_str in d_strs:
            d.append(d_str)

    d = [int(num) for num in d]
    mdy = [my + timedelta(days=item-1) for item in d]

    ## Further, we want check in and checkout times to be associated with these dates.

    checkin = re.findall(r'Check-In\s(\d{2}:\d{2})', pairing)
    checkin = datetime.strptime(checkin[0],"%H:%M")
    checkins = list()
    for date in mdy:
        checkin_datetime = datetime.combine(date.date(), checkin.time())
        checkins.append(checkin_datetime)

    checkout = re.findall(r'Check-Out\s(\d{2}:\d{2})', pairing)
    checkout = datetime.strptime(checkout[0],"%H:%M")
    checkouts = list()
    for date in mdy:
        date = date + timedelta(days = n_days - 1)
        checkout_datetime = datetime.combine(date.date(), checkout.time())
        checkouts.append(checkout_datetime)

    ## Now all that remains is to make our table_data with all pairings. But because we want to filter by dates, we actually make an observation for each date a pairing is offered as well.

    checkinouts = []
    for item1, item2 in zip(checkins, checkouts):
        checkinouts.append((item1, item2))
    
    for checkinout in checkinouts:
        checkin, checkout = checkinout
        obs = pd.DataFrame([[p_code, n_days, checkin, checkout, credit_sum, block_sum, softtime, tafb, flight_data]], columns = table_columns)
        table_data = pd.concat([table_data, obs], ignore_index=True)

table_data['flight_data'] = table_data['flight_data'].astype(str)


####

@app.callback(
    Output('datatable', 'data'),
    [Input('my-date-picker-range', 'start_date'), Input('my-date-picker-range', 'end_date')],
    [State('data-store', 'data')]
)
def date_filter_table(start_date, end_date, data):
    if start_date is not None and end_date is not None:
        start_date_object = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_object = datetime.strptime(end_date, '%Y-%m-%d')

        table_data['checkin'] = pd.to_datetime(table_data['checkin'])
        table_data['checkout'] = pd.to_datetime(table_data['checkout'])

        filtered_data = table_data[
            (table_data['checkin'].dt.date >= start_date_object.date()) &
            (table_data['checkout'].dt.date <= end_date_object.date())
        ]

        filtered_data['checkin'] = filtered_data['checkin'].dt.strftime('%m-%d-%Y, %H:%M')
        filtered_data['checkout'] = filtered_data['checkout'].dt.strftime('%m-%d-%Y, %H:%M')
        
        return filtered_data.to_dict('records')
    
    #table_data['checkin'] = pd.to_datetime(table_data['checkin'])
    #table_data['checkout'] = pd.to_datetime(table_data['checkout'])

    table_data['checkin'] = table_data['checkin'].dt.strftime('%m-%d-%Y, %H:%M')
    table_data['checkout'] = table_data['checkout'].dt.strftime('%m-%d-%Y, %H:%M')

    datatable_data = table_data.to_dict('records')
    return datatable_data

@app.callback(
    Output('selected_row_store', 'data'),
    Output('selected_row_table', 'children'),
    Input('datatable', 'active_cell'),
    Input('datatable', 'data'),
    State('datatable', 'derived_virtual_indices')
)
def update_selected_row(active_cell, data, derived_virtual_indices):
    selected_row_index = active_cell['row'] if active_cell else None
    selected_row_table = None

    print(len(data))
    print(len(derived_virtual_indices))

    if selected_row_index is not None:
        if derived_virtual_indices and selected_row_index >= len(derived_virtual_indices):
            selected_row_index = None

        if selected_row_index is not None:
            if derived_virtual_indices:
                selected_row_index = derived_virtual_indices[selected_row_index]
            else:
                selected_row_index = None

            if selected_row_index is not None:
                selected_p_code = data[selected_row_index]['p_code']
                selected_data = table_data[table_data['p_code'] == selected_p_code]

                if not selected_data.empty:
                    selected_table = selected_data.iloc[0]['flight_data']
                    selected_df = pd.DataFrame(eval(selected_table), columns=flight_columns)
                    selected_row_table = dash_table.DataTable(
                        columns=[{"name": col, "id": col} for col in flight_columns],
                        data=selected_df.to_dict('records'),
                        style_table={'overflowX': 'auto'}
                    )

    return selected_row_index, selected_row_table