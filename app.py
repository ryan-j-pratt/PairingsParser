from dash import dash, html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import re
import pandas as pd
from datetime import datetime, timedelta
import base64
import json

table_columns = ['p_code', 'n_days', 'checkin', 'checkout', 'credit_sum', 'block_sum', 'softtime','tafb','flight_data']
#table_data = pd.DataFrame(columns=table_columns)

flight_columns = ['Day', 'Flt', 'Dep', 'Local_Dep', 'Arr', 'Local_Arr', 'Turn', 'Eqp', 'Block']

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

#exec(open("predata.py").read())

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
                        html.H1("Title"),
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
                                multiple=False  # Set to True if you want to allow multiple file uploads
                            ),
                            html.Div(id='output-data-upload')
                        ])
                    ],
                    className='col-md-8'
                ),
                dbc.Col(
                    [
                        html.H2("Header"),
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
                            id='output-data-table'
                        )
                        #dcc.Store(id='data-store'),
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
                                html.H3("Other Information"),
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

@app.callback(
    [Output('output-data-upload', 'children'), Output('output-data-table', 'children')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def process_uploaded_file(contents, filename):
    if contents is not None:
        # Read the file contents
        file_content = contents.encode("utf8").split(b";base64,")[1]
        decoded_content = base64.b64decode(file_content).decode("utf8")
        
        # Remove line breaks and create a continuous string
        file_contents = decoded_content.replace("\n", "")
    else:
        # Set a default value if no file is uploaded
        file_contents = '''
            ----------------------------------------------------------------------------------------------------
            Z2071  Check-In 09:22   Check-Out 13:08            4-Day                     OCT 2022
                                                                                        +---------------------+
            Day    Flt   Dep  Local   Arr  Local   Turn     Eqp   Block      Duty        | S  M  T  W  T  F  S |
            1     2176  EWR  07:12   HOU  11:14   001:00   32M   004:14                 |=====================|
            1     1149  HOU  12:14   EWR  16:19            32M   004:05                 |         -- -- -- -- |
            EWR   009:43  Renaissance EWR Airport       908-437-4600      008:33      |-- -- -- -- -- -- 14 |
            2     1831  EWR  09:21   DFW  12:20   001:00   32M   002:59                 |13 -- -- -- -- -- 19 |
            2     2086  DFW  13:20   EWR  17:13            32M   003:53                 |-- 22 23 -- -- 26 -- |
            EWR   008:07  Renaissance EWR Airport       908-437-4600      006:51      |-- -- 33 -- -- --    |
            3     1863  EWR  10:01   MCO  12:53            32M   002:52                 +---------------------+
            MCO   023:56  Courtyard Orlando Downtown     407-996-1000      003:52
            4     1894  MCO  11:20   EWR  15:13            32M   003:53    
                                                                            004:53
                                                                ----------------------
            Credit: 027:46                                        023:19     031:12
            TAFB: 083:28
            Crew Comp:  1 CA, 1 FO
            ----------------------------------------------------------------------------------------------------
            END
            '''


    pairings = file_contents.split('----------------------------------------------------------------------------------------------------')
    del pairings[0]
    del pairings[-1]

    table_data = pd.DataFrame(columns=table_columns)

    for pairing in pairings:
        #global table_data

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
        d_list = re.findall(r'\|(\d{2})\s|\s(\d{2})\s', pairing)
        print(d_list)

        d = [int(num) for tup in d_list for num in tup if num]
        print(d)
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
            obs = pd.DataFrame([[p_code, n_days, checkin, checkout, credit_sum, block_sum, softtime, tafb, flight_data]], columns = table_columns)
            table_data = pd.concat([table_data, obs], ignore_index=True)

        table_data['flight_data'] = table_data['flight_data'].astype(str)

        table_data['checkin'] = pd.to_datetime(table_data['checkin'])
        table_data['checkout'] = pd.to_datetime(table_data['checkout'])

    data_table = dash_table.DataTable(
            id='datatable',
            columns=[{"name": col, "id": col} for col in table_data.columns[[0] + list(range(2, 5))]],
            data=table_data.to_dict('records'),
            sort_action='native',
            sort_mode='multi',
        )

    output_message = f'{filename} successfully processed. Pairings found: {len(pairings)}'

    return output_message, data_table

if __name__ == '__main__':
    app.run_server(debug=True)
