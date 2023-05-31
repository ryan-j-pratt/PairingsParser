from dash import dash, html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import re
import pandas as pd
from datetime import datetime, timedelta
import base64
import json

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

# Create the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])
app.title = 'Parser'
server = app.server

import dash_bootstrap_components as dbc

app.layout = dbc.Container(
    fluid=True,
    className='container',
    children=[
        dbc.Row(
            [
                html.H1("Pairings Parser"),
                dcc.Store(id='selected_row_store'),
                dcc.Markdown(
                            '''
                            This web app is designed to provide an interactive interface for exploring pairing data. 
                            Pairings are displayed on the left and can be filtered and sorted. 
                            Full details appear on the right when you click on a row. 
                            Feel free to get started with the preloaded data, or upload your own.
                            '''
                        ),
            ],
            className='row',
            style={'textAlign':'center'}
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Upload(
                                id='upload-data',
                                children=html.Div([
                                    'Drag and Drop or ',
                                    html.A('Select Files')
                                ]),
                                style={
                                    'width': '95%',
                                    'height': '60px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'margin': '10px'
                                },
                                multiple=False
                            ),
                        html.Div(
                                id='output-data-upload',
                                style={
                                    'margin': '10px'
                                    }
                            ),
                        html.Div(
                            [
                                "Select date range: ",
                                dcc.DatePickerRange(
                                    id='my-date-picker-range',
                                    clearable=True,
                                    minimum_nights=0,
                                    start_date_placeholder_text="Start Date",
                                    end_date_placeholder_text="End Date"
                                ),
                            ],
                            style={'margin':'10px'}
                        ),
                        html.Div(
                            [
                                "Select number of days:",
                                dcc.RangeSlider(
                                        id='range-slider',
                                        value=[1, 5],
                                        step=1,
                                        marks={i: str(i) for i in range(1,6)},
                                        allowCross=False,
                                        updatemode='drag'
                                    ),
                            ],
                            style={'margin':'10px'}
                        ),
                        html.Div(
                            id='output-data-table',
                            children=dash_table.DataTable(
                                id='datatable',
                                columns=[{"name": col, "id": col_id} for col, col_id in zip(display_columns[0:4],table_columns[0:4])],
                                data=[],
                                sort_action='native',
                                sort_mode='multi',
                                style_data_conditional=[]
                                )
                            )
                    ],
                    className='col-md-5'
                ),
                dbc.Col(
                    [
                        html.Div(
                            [],
                            id='selected_row_info'
                        ),
                    ],
                    className='col-md-7'
                ),
            ],
            className='row',
        ),
        dbc.Row(
            [
                html.Div(
                            [
                                dcc.Markdown(
                                    '''
                                    For more information about this project you can visit its [GitHub repo](https://github.com/ryan-j-pratt/pairings-parser/tree/main).
                                    '''
                                ),
                            ],
                            className='about-section',
                            style={'margin':'10px'}
                        ),
            ],
            className='row',
            style={'textAlign':'center'}
        ),
    ],
)

@app.callback(
    [Output('output-data-upload', 'children'), 
     Output('datatable', 'data')],
    [Input('upload-data', 'contents')],
    [Input('my-date-picker-range', 'start_date'), Input('my-date-picker-range', 'end_date')],
    [Input('range-slider', 'value')],
    [State('upload-data', 'filename')]
)
def process_uploaded_file(contents, start_date, end_date, range_values, filename):
    if contents is not None:
        # Read the file contents
        file_content = contents.encode("utf8").split(b";base64,")[1]
        decoded_content = base64.b64decode(file_content).decode("utf8")
        
        # Remove line breaks and create a continuous string
        file_contents = decoded_content.replace("\n", "")
    else:
        # Set a default value if no file is uploaded
        # Read the JSON file
        with open('default_data.json', 'r') as file:
            serialized_data = file.read()

        # Deserialize the JSON data
        data_list = json.loads(serialized_data)

        # Convert millisecond timestamps to datetime objects
        for data in data_list:
            data['checkin'] = pd.to_datetime(data['checkin'], unit='ms')
            data['checkout'] = pd.to_datetime(data['checkout'], unit='ms')

        # Create a dataframe from the data
        table_data = pd.DataFrame(data_list)

        output_message = 'Default data used'

    if range_values is not None:
        filtered_data = table_data.loc[(table_data['n_days'] >= range_values[0]) & (table_data['n_days'] <= range_values[1])]
    else:
        filtered_data = table_data.copy()  # Create a copy of the original table_data

    if start_date is not None and end_date is not None:
        start_date_object = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_object = datetime.strptime(end_date, '%Y-%m-%d')

        filtered_data['checkin'] = pd.to_datetime(filtered_data['checkin'])
        filtered_data['checkout'] = pd.to_datetime(filtered_data['checkout'])

        filtered_data = filtered_data[
            (filtered_data['checkin'].dt.date >= start_date_object.date()) &
            (filtered_data['checkout'].dt.date <= end_date_object.date())
        ]

    filtered_data.loc[:, 'checkin'] = filtered_data['checkin'].dt.strftime('%m/%d, %H:%M')
    filtered_data.loc[:, 'checkout'] = filtered_data['checkout'].dt.strftime('%m/%d, %H:%M')


    return output_message, filtered_data.to_dict('records')

@app.callback(
    Output('selected_row_store', 'data'),
    Output('selected_row_info', 'children'),
    Input('datatable', 'active_cell'),
    Input('datatable', 'data'),
    State('datatable', 'derived_virtual_indices')
)
def update_selected_row(active_cell, table_data, derived_virtual_indices):
    table_data = pd.DataFrame(table_data)
    selected_row_index = active_cell['row'] if active_cell else None
    selected_row_info = None

    if selected_row_index is not None:
        if derived_virtual_indices and selected_row_index >= len(derived_virtual_indices):
            selected_row_index = None

        if selected_row_index is not None:
            if derived_virtual_indices:
                selected_row_index = derived_virtual_indices[selected_row_index]
            else:
                selected_row_index = None

            if selected_row_index is not None:
                selected_data = table_data.iloc[selected_row_index]

                selected_p_code = selected_data['p_code']
                selected_checkin = selected_data['checkin']
                selected_checkout = selected_data['checkout']
                selected_tafb = selected_data['tafb']
                selected_credit = selected_data['credit_sum']
                selected_block = selected_data['block_sum']
                selected_soft = selected_data['softtime']

                selected_atts = f"Code: {selected_p_code}\nCheck-In: {selected_checkin} \u2014 Check-Out: {selected_checkout}\nTAFB: {selected_tafb}\nCredit: {selected_credit} - Block: {selected_block} = Soft: {selected_soft}"

                selected_table = selected_data['flight_data']
                selected_df = pd.DataFrame(eval(selected_table), columns=flight_columns)
                selected_row_table = dash_table.DataTable(
                    columns=[{"name": col, "id": col} for col in flight_columns],
                    data=selected_df.to_dict('records'),
                    style_table={'overflowX': 'auto'}
                )
                selected_row_info = [
                    html.H4('Pairing Info'),
                    html.Div(selected_atts, style={'white-space': 'pre-wrap'}),
                    html.H5('Flight Table'),
                    selected_row_table,
                ]

    return selected_row_index, selected_row_info

if __name__ == '__main__':
    app.run_server(debug=True)
