# Pairings Parser

This web app provides an interactive interface for exploring pairing data. It is built entirely with Python using Dash by Plotly and allows users to upload their own pairings as a .txt file, sort and filter the data, and view detailed information about each pairing. Whether you're a pilot preparing a bid or simply interested in analyzing pairing data, Pairings Parser makes the process easier and more convenient.

## Usage

The easiest way to get started with the pairings parser is to visit an instance of it online. You can find a copy at [render.com](). Alternatively, you can read on to find info on running the program locally. Advanced users can also deploy it on their own server.

Once you have the web app up and running, follow these instructions to use the Pairings Parser:

Upload Pairings: Click on the "Upload" button and select a .txt file containing the pairings data. The app will process the file and display the pairings on the left side of the interface.

Sort and Filter: Use the sorting and filtering options provided to organize the pairings based on code, check-in and check-out dates and times, and total credit hours. This will help you quickly find the pairings that meet your criteria.

View Details: Click on a row in the pairing list to see full details on the right side of the interface. This includes information such as code, check-in and check-out dates and times, time away from base, total credit hours, block time, soft time, and a table of all flights.

Date and Duration Filters: Use the calendar date picker and duration slider to filter the pairings based on specific date ranges and trip lengths in days. This allows you to narrow down the results and focus on the pairings that match your preferences.

## Installation

To run the Pairings Parser web app locally, follow these steps:

Clone the repository to your local machine:

`git clone https://github.com/your-username/pairings-parser.git`

Navigate to the project directory:

`cd pairings-parser`

Install the required dependencies using pip:

`pip install -r requirements.txt`

Run the app:

`python app.py`

And finally, open your web browser and visit http://localhost:8050 to access the Pairings Parser web app.

## Development

### Current features:
- Upload your own pairings as a .txt file
- Sort by code, check-in and check-out dates and times, and total credit hours
- View pairing information including code, check-in and check-out dates and times, time away from base, total credit hours, block time, soft time, and a table of all flights
- Filter by calendar dates and length of trip in days

### Planned features:
- Toggle to display only trips with soft time
- Filter by layover destination

## Troubleshooting

Problem: Nothing happens when I upload a .txt file!

Solution: The program was developed using pairing data from one major airline so it may not work for all pairing .txt files.

For any other questions, feedback, or support, please feel free to contact the developer at your-email@example.com.

## About
This project was first put together in a couple days in May 2023. Captain Jim Pratt is a long-time pilot with a major airline and his son figured he could spend some time with Python to make sorting and filtering pairings and preparing a bid a little easier. Both learned some things along the way.

## License

This project is licensed under the [MIT License](https://github.com/ryan-j-pratt/pairings-parser/blob/e78d2ed42db588364a3d217577d76127e3706b58/LICENSE).