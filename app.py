from dash import dash, html, dcc, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import re
import pandas as pd
from datetime import datetime, timedelta
import base64

#execfile("confidential.py")

table_columns = ['p_code', 'n_days', 'checkin', 'checkout', 'credit_sum', 'block_sum', 'softtime','tafb','flight_data']
table_data = pd.DataFrame(columns=table_columns)

flight_columns = ['Day', 'Flt', 'Dep', 'Local_Dep', 'Arr', 'Local_Arr', 'Turn', 'Eqp', 'Block']

file_contents = '''----------------------------------------------------------------------------------------------------
        E2001  Check-In 05:14   Check-Out 13:50            1-Day                     SEP 2022
                                                                                    +---------------------+
        Day    Flt   Dep  Local   Arr  Local   Turn     Eqp   Block      Duty        | S  M  T  W  T  F  S |
        1     2295  EWR  06:14   MIA  09:18   001:07   32M   003:04                 |=====================|
        1     2594  MIA  10:25   EWR  13:35            32M   003:10                 |         -- -- -- 03 |
                                                                        008:36      |04 -- -- -- -- -- -- |
                                                            ----------------------   |-- -- -- -- -- -- -- |
        Credit: 006:14                                        006:14     008:36      |-- -- -- -- -- -- -- |
        TAFB: 008:36                                                                 |-- -- -- -- -- --    |
        Crew Comp:  1 CA, 1 FO                                                       +---------------------+
        ----------------------------------------------------------------------------------------------------
        E2002  Check-In 05:59   Check-Out 14:09            1-Day                     SEP 2022
                                                                                    +---------------------+
        Day    Flt   Dep  Local   Arr  Local   Turn     Eqp   Block      Duty        | S  M  T  W  T  F  S |
        1     1711  EWR  06:59   RSW  09:57   001:03   32M   002:58                 |=====================|
        1     1712  RSW  11:00   EWR  13:54            32M   002:54                 |         -- -- -- -- |
                                                                        008:10      |-- -- -- 07 08 09 -- |
                                                            ----------------------   |11 12 -- 14 -- 16 -- |
        Credit: 005:52                                        005:52     008:10      |18 19 20 21 22 23 -- |
        TAFB: 008:10                                                                 |25 26 27 -- 29 30    |
        Crew Comp:  1 CA, 1 FO                                                       +---------------------+
        ----------------------------------------------------------------------------------------------------
        E2087  Check-In 14:21   Check-Out 07:05            5-Day                     SEP 2022
                                                                                    +---------------------+
        Day    Flt   Dep  Local   Arr  Local   Turn     Eqp   Block      Duty        | S  M  T  W  T  F  S |
        1     1493  EWR  15:21   STI  19:09   001:00   32M   003:48                 |=====================|
        1     0194  STI  20:09   EWR  23:59            32M   003:50                 |         -- -- -- -- |
        EWR   014:15  Renaissance EWR Airport       908-436-4600      009:53      |-- -- 06 -- -- -- -- |
        2     1493  EWR  15:14   STI  18:59   001:00   32M   003:45                 |-- -- -- -- -- -- -- |
        2     0194  STI  19:59   EWR  23:42            32M   003:43                 |-- -- -- -- -- -- -- |
        EWR   020:18  The Westin Jersey City Ne     201-626-2900      009:28      |-- -- -- -- -- --    |
        3     1003  EWR  21:00   SDQ  00:48            32M   003:48                 +---------------------+
        SDQ   025:02  Sheraton Santo Domingo        809 221 6666      004:48
        5     1004  SDQ  02:50   EWR  06:50            32M   004:00    
                                                                        005:00
                                                            ----------------------
        Credit: 025:21                                        022:54     029:09
        TAFB: 088:44
        Crew Comp:  1 CA, 1 FO
        ----------------------------------------------------------------------------------------------------
        END
        '''

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

# Create the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])



import dash_bootstrap_components as dbc

app.layout = dbc.Container(
    fluid=True,
    className='container',
    children=[
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2("Header"),
                        html.P("Instructions"),
                        dcc.Store(id='selected_row_store'),
                        dcc.DatePickerRange(
                            id='my-date-picker-range',
                            clearable=True,
                            minimum_nights=0,
                            start_date_placeholder_text="Start Date",
                            end_date_placeholder_text="End Date"
                        ),
                        html.Div(id='output-container-date-picker-range'),
                        html.Div([
                            dcc.Upload(
                                id='upload-data',
                                children=html.Div([
                                    'Drag and Drop or ',
                                    html.A('Select Files')
                                ]),
                                style={
                                    'width': '100%',
                                    'height': '60px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'margin': '10px'
                                },
                                multiple=False  # Set to True if you want to allow multiple file uploads
                            ),
                            html.Div(id='output-data-upload')
                        ])
                    ],
                    className='col-md-8'
                ),
                dbc.Col(
                    [
                        html.H2("Title"),
                    ],
                    className='col-md-4'
                ),
            ],
            className='row',
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dash_table.DataTable(
                            id='datatable',
                            columns=[{"name": col, "id": col} for col in table_data.columns[[0] + list(range(2, 5))]],
                            data=table_data.to_dict('records'),
                            sort_action='native',
                            sort_mode='multi',
                            #className='table table-striped'
                        ),
                    ],
                    className='col-md-8'
                ),
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H3("Flight Table"),
                            ],
                            id='selected_row_table'
                        ),
                        # Other information here
                    ],
                    className='col-md-4'
                ),
            ],
            className='row',
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H3("About Information"),
                            ],
                            className='about-section'
                        ),
                    ],
                    className='col-md-8'
                ),
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H3("About Information"),
                            ],
                            className='about-section'
                        ),
                    ],
                    className='col-md-4'
                ),
            ],
            className='row',
        ),
    ],
)

@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'))
def process_uploaded_file(contents, filename):
    if contents is not None:
        # Read the file contents
        file_content = contents.encode("utf8").split(b";base64,")[1]
        decoded_content = base64.b64decode(file_content).decode("utf8")
        
        # Remove line breaks and create a continuous string
        file_contents = decoded_content.replace("\n", "")
    else:
        # Set a default value if no file is uploaded
        file_contents = '''----------------------------------------------------------------------------------------------------
        E2001  Check-In 05:14   Check-Out 13:50            1-Day                     SEP 2022
                                                                                    +---------------------+
        Day    Flt   Dep  Local   Arr  Local   Turn     Eqp   Block      Duty        | S  M  T  W  T  F  S |
        1     2295  EWR  06:14   MIA  09:18   001:07   32M   003:04                 |=====================|
        1     2594  MIA  10:25   EWR  13:35            32M   003:10                 |         -- -- -- 03 |
                                                                        008:36      |04 -- -- -- -- -- -- |
                                                            ----------------------   |-- -- -- -- -- -- -- |
        Credit: 006:14                                        006:14     008:36      |-- -- -- -- -- -- -- |
        TAFB: 008:36                                                                 |-- -- -- -- -- --    |
        Crew Comp:  1 CA, 1 FO                                                       +---------------------+
        ----------------------------------------------------------------------------------------------------
        E2087  Check-In 14:21   Check-Out 07:05            5-Day                     SEP 2022
                                                                                    +---------------------+
        Day    Flt   Dep  Local   Arr  Local   Turn     Eqp   Block      Duty        | S  M  T  W  T  F  S |
        1     1493  EWR  15:21   STI  19:09   001:00   32M   003:48                 |=====================|
        1     0194  STI  20:09   EWR  23:59            32M   003:50                 |         -- -- -- -- |
        EWR   014:15  Renaissance EWR Airport       908-436-4600      009:53      |-- -- 06 -- -- -- -- |
        2     1493  EWR  15:14   STI  18:59   001:00   32M   003:45                 |-- -- -- -- -- -- -- |
        2     0194  STI  19:59   EWR  23:42            32M   003:43                 |-- -- -- -- -- -- -- |
        EWR   020:18  The Westin Jersey City Ne     201-626-2900      009:28      |-- -- -- -- -- --    |
        3     1003  EWR  21:00   SDQ  00:48            32M   003:48                 +---------------------+
        SDQ   025:02  Sheraton Santo Domingo        809 221 6666      004:48
        5     1004  SDQ  02:50   EWR  06:50            32M   004:00    
                                                                        005:00
                                                            ----------------------
        Credit: 025:21                                        022:54     029:09
        TAFB: 088:44
        Crew Comp:  1 CA, 1 FO
        ----------------------------------------------------------------------------------------------------
        END
        '''


        pairings = file_contents.split('----------------------------------------------------------------------------------------------------\n')
        del pairings[0]
        del pairings[-1]

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
            
            table_data = pd.DataFrame(columns=table_columns)

            for checkinout in checkinouts:
                checkin, checkout = checkinout
                obs = pd.DataFrame([[p_code, n_days, checkin, checkout, credit_sum, block_sum, softtime, tafb, flight_data]], columns = table_columns)
                table_data = pd.concat([table_data, obs], ignore_index=True)

        table_data['flight_data'] = table_data['flight_data'].astype(str)        


        return html.Div([
            html.H5(f"Uploaded File: {filename}"),
            #html.H6("File Content:"),
            #html.Pre(decoded_content[:200] + "...")
        ])

@app.callback(
    Output('datatable', 'data'),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
)
def update_table(start_date, end_date):
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
    
    table_data['checkin'] = pd.to_datetime(table_data['checkin'])
    table_data['checkout'] = pd.to_datetime(table_data['checkout'])

    table_data['checkin'] = table_data['checkin'].dt.strftime('%m-%d-%Y, %H:%M')
    table_data['checkout'] = table_data['checkout'].dt.strftime('%m-%d-%Y, %H:%M')

    return table_data.to_dict('records')

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


if __name__ == '__main__':
    app.run_server(debug=True)
