import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px

from sodapy import Socrata

import helper as help



@st.cache_data(persist=True)
def load_data(nrows: int) -> pd.DataFrame:
    '''
    This function imports data through SODA API and does some cleaning
    ...
    var nrows: Number of records to be loaded into the dataframe
    type: int
    ...
    return: A dataframe with the data on several incidents in NYC
    rtype: pd.DataFrame
    '''
    client = Socrata("data.cityofnewyork.us", None)
    client.timeout = 1000
    results = client.get("h9gi-nx95", limit=nrows)
    df = pd.DataFrame.from_records(results)
    return df


def scrub_data(df: pd.DataFrame) -> pd.DataFrame:
    '''
    This function cleans the dataset before analyzing it
    ...
    var df: Pre-processed dataframe with the data on several incidents in NYC
    type: pd.DataFrame
    ...
    return: Processed dataframe with the data on several incidents
    rtype: pd.DataFrame
    '''
    # Parse Date and Time
    df['crash_date'] = pd.to_datetime(df['crash_date']).dt.strftime('%Y-%m-%d') 
    df['crash_time'] = pd.to_datetime(df['crash_time'], format='%H:%M').dt.time
    df['crash_date_crash_time'] = pd.to_datetime(df['crash_date'].astype(str) + ' ' + df['crash_time'].astype(str), format = '%Y-%m-%d %H:%M:%S')

    # Drop superfluous data and Rename Columns
    df.dropna(subset=['latitude', 'longitude'], inplace=True)
    lowercase = lambda x: str(x).lower()
    df.rename(lowercase, axis="columns", inplace=True)
    df.columns = df.columns.str.replace(' ', '_')
    df.rename(columns={"crash_date_crash_time": "date/time"}, inplace=True)

    # Convert strings to numerical data
    numeric_data = (['number_of_persons_injured', 'number_of_pedestrians_injured', 'number_of_cyclist_injured', 'number_of_motorist_injured',
                     'number_of_persons_killed', 'number_of_pedestrians_killed', 'number_of_cyclist_killed', 'number_of_motorist_killed'])
    df[numeric_data] = df[numeric_data].apply(pd.to_numeric, errors='coerce')
    df['latitude'] = df['latitude'].astype(float)
    df['longitude'] = df['longitude'].astype(float)

    # Include the data only from NYC metro area
    nyc_latitude_min = 40.4
    nyc_latitude_max = 41.0
    nyc_longitude_min = -74.3
    nyc_longitude_max = -73.7
    df = (df[(df['latitude'] >= nyc_latitude_min) & (df['latitude'] <= nyc_latitude_max) &
                (df['longitude'] >= nyc_longitude_min) & (df['longitude'] <= nyc_longitude_max)])
    return df


def map_of_the_incident(df: pd.DataFrame) -> None:
    '''
    This function plots the data points of the incident on the map and proides options to view raw data and analyze it
    ...
    var df: Data on a certain mototr incident in NYC
    type: pd.DataFrame
    ...
    return: Plots the data points on the map
    rtype: None
    '''
    
    st.header("Visualize data based on the type of incident")
    select = st.selectbox('', (['Total Injured', 'Pedestrians Injured', 'Cyclists Injured', 'Motorists Injured', 
                               'Total Killed', 'Pedestrians Killed', 'Cyclists Killed', 'Motorists Killed']))
   
    # Extract the data
    num_people = st.slider("Number of persons injured in vehicle collisions", min_value=0, max_value=15, value=1)
    if select == 'Total Injured':
        query_data = df.query("number_of_persons_injured >= @num_people")[["latitude", "longitude"]].dropna(how="any")
    elif select == 'Pedestrians Injured':
        query_data = df.query("number_of_pedestrians_injured >= @num_people")[["latitude", "longitude"]].dropna(how="any")
    elif select == 'Cyclists Injured':
        query_data = df.query("number_of_cyclist_injured >= @num_people")[["latitude", "longitude"]].dropna(how="any")
    elif select == 'Motorists Injured':
        query_data = df.query("number_of_motorist_injured >= @num_people")[["latitude", "longitude"]].dropna(how="any")
    elif select == 'Total Killed':
        query_data = df.query("number_of_persons_killed >= @num_people")[["latitude", "longitude"]].dropna(how="any")
    elif select == 'Pedestrians Killed':
        query_data = df.query("number_of_pedestrians_killed >= @num_people")[["latitude", "longitude"]].dropna(how="any")
    elif select == 'Cyclists Killed':
        query_data = df.query("number_of_cyclist_killed >= @num_people")[["latitude", "longitude"]].dropna(how="any")
    elif select == 'Motorists Killed':
        query_data = df.query("number_of_motorist_killed >= @num_people")[["latitude", "longitude"]].dropna(how="any")

    # Plot the map
    st.map(query_data, zoom=12)

    # Raw data check-box for this map
    if st.checkbox("Show raw data", value=False, key=1.1):
        st.subheader("Raw data of " + "'" + str(select) + "'")
        st.write(df)

    # Analysis check-box for the data selected for this map
    if st.checkbox("Analyze the data for " + "'" + str(select) + "'", value=True, key=1.2):
        st.header("Analysis of the data for " + "'" + str(select) + "'")
        help.exploratory_data_analysis(df)


def map_of_the_incident_freq_hist(df: pd.DataFrame) -> int:
    '''
    This function plots a certain motor incident frequency histograms on the map
    ...
    var df: Data on a certain motor incident in NYC
    type: pd.DataFrame
    ...
    return: The starting hour of the incident selected by the user
    rtype: int
    '''
    
    st.header("How many collisions occur during a given time of day? (24-hour clock)")
    hour = st.slider("Hour to look at", min_value=0, max_value=23, value=17)
    df = df[df["date/time"].dt.hour == hour]
    st.markdown("Vehicle collisions between %i:00 and %i:00" % (hour, (hour + 1) % 24))
    # New York City coordinates
    latitude, longitude = 40.7128, -74.0060
    midpoint = (latitude, longitude) # Point the initial view of the map to New york city
    # Map customization: centering and area
    st.write(pdk.Deck(
        map_style="mapbox://styles/mapbox/streets-v12", # mapbox://styles/mapbox/light-v9
        initial_view_state={
            "latitude": midpoint[0],
            "longitude": midpoint[1],
            "zoom": 11,
            "pitch": 50,
        },
        layers=[
            pdk.Layer(
            "HexagonLayer",
            data=df[['date/time', 'latitude', 'longitude']],
            get_position=["longitude", "latitude"],
            auto_highlight=True,
            radius=100,
            extruded=True,
            pickable=True,
            elevation_scale=4,
            elevation_range=[0, 1000],
            ),
        ],
    ))
    # Raw data check-box for this map
    if st.checkbox("Show raw data", value=False, key=2):
        st.subheader("Raw data by minute between %i:00 and %i:00" % (hour, (hour + 1) % 24))
        st.write(df)
    return hour


def gen_chart_hist_by_min(df: pd.DataFrame, hour) -> None:
    '''
    This function plots histograms based on frequency of the incident by each minute in the time specified by user
    ...
    var df: Data on a certain motor incident in NYC
    type: pd.DataFrame

    var hour: The starting hour of the incident selected by the user
    type: int
    ...
    return: Plots the incident frequency histograms on the map
    rtype: None
    '''

    st.subheader("Breakdown by minute between %i:00 and %i:00" % (hour, (hour + 1) % 24))
    filtered = df[
        (df["date/time"].dt.hour >= hour) & (df["date/time"].dt.hour < (hour + 1))
    ]
    hist = np.histogram(filtered["date/time"].dt.minute, bins=60, range=(0, 60))[0]
    chart_data = pd.DataFrame({"minute": range(60), "crashes": hist})
    fig = px.bar(chart_data, x='minute', y='crashes', hover_data=['minute', 'crashes'], height=400)
    st.write(fig)


def create_table_incident_by_street(df: pd.DataFrame) -> None:
    '''
    This function creates a table for the top 5 streets for the specified incident 
    ...
    var df: Data on a certain motor incident in NYC
    type: pd.DataFrame
    ...
    return: Creates a table for the top 5 streets for the specified incident on the map
    rtype: None
    '''

    st.header("Top 5 dangerous streets by affected class")
    select = st.selectbox('Affected class', ['Pedestrians', 'Cyclists', 'Motorists'])
    if select == 'Pedestrians':
        st.write(df.query("number_of_pedestrians_injured >= 1")[["on_street_name", "number_of_pedestrians_injured"]].sort_values(by=['number_of_pedestrians_injured'], ascending=False).dropna(how="any")[:5])
    elif select == 'Cyclists':
        st.write(df.query("number_of_cyclist_injured >= 1")[["on_street_name", "number_of_cyclist_injured"]].sort_values(by=['number_of_cyclist_injured'], ascending=False).dropna(how="any")[:5])
    else:
        st.write(df.query("number_of_motorist_injured >= 1")[["on_street_name", "number_of_motorist_injured"]].sort_values(by=['number_of_motorist_injured'], ascending=False).dropna(how="any")[:5])


def gen_dashboard(nrows: int) -> None:
    '''
    This is the main function that creates the whole app: plots maps, generates charts, and creates tables
    ...
    var nrows: Number of records to be loaded into the dataframe
    type: int
    ...
    return: Creates the whole app: plots maps, generates charts, and creates tables
    rtype: None
    '''
    st.set_page_config(
        page_title="Motor Vehicle Collisions",
        page_icon="🤖",
        layout="wide"
    )
    

    st.title("Visualization and Exploratory Data Analysis (EDA) of Motor Vehicle Collisions in New York City, USA")
    st.markdown("This application is a Streamlit dashboard hosted on the Streamlit cloud server that can be used "
                "to analyze motor vehicle collisions in NYC 🗽")
    help.space(4)

    data = load_data(nrows)
    data = scrub_data(data)

    # Map-1: Plots the data points of the incident on the map
    map_of_the_incident(data)
    help.space(4)

    # Map-2: Plots histograms based on frequency of the incident on the map 
    hour = map_of_the_incident_freq_hist(data)
    help.space(4)

    # Chart: Plots histograms based on frequency of the incident by each minute in the specified time on time-axis 
    gen_chart_hist_by_min(data, hour)
    help.space(4)

    # Table: Creates a table for the top 5 streets for the specified incident 
    create_table_incident_by_street(data)


if __name__ == '__main__':
    gen_dashboard(10000)
