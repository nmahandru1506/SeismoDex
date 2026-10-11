import streamlit as st
import pandas as pd

st.title("SeismoDex")

url = ("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.csv")

earthquakes = pd.read_csv(url)


regions = {"Asia": {"min_lat": -10,
                    "max_lat": 80,
                    "min_lon": 25,
                    "max_lon": 180},
           "Europe": {"min_lat": 35,
                      "max_lat": 72,
                      "min_lon": -25,
                      "max_lon": 45},
           "North America": {"min_lat": 7,
                             "max_lat": 83,
                             "min_lon": -170,
                             "max_lon": -50},
           "South America": {"min_lat": -55,
                             "max_lat": 12,
                             "min_lon": -82,
                             "max_lon": -35},
           "Africa": {"min_lat": -34,
                      "max_lat": 39,
                      "min_lon": -17,
                      "max_lon": 50},
           "Antarctica": {"min_lat": -90,
                          "max_lat": -60,
                          "min_lon": -180,
                          "max_lon": 180},
           "Oceania": {"min_lat": -50,
                       "max_lat": 10,
                       "min_lon": 110,
                       "max_lon": 180}}


def get_region(region, min_magnitude, max_depth):
    boundaries = regions[region]
    region_data = earthquakes[
      (earthquakes["latitude"] >= boundaries["min_lat"]) &
      (earthquakes["latitude"] <= boundaries["max_lat"]) &
      (earthquakes["longitude"] >= boundaries["min_lon"]) &
      (earthquakes["longitude"] <= boundaries["max_lon"]) &
      (earthquakes["mag"] >= min_magnitude) &
      (earthquakes["depth"] <= max_depth)]
    return region_data


region = st.selectbox("Choose a region", ["Asia", "Europe", "North America", "South America", "Africa", "Antarctica", "Oceania"])
min_magnitude = st.slider("Minimum magnitude", min_value=2.5, max_value=8.0, value=4.0, step=0.1)
max_depth = st.slider("Maximum depth", min_value=0, max_value=656, value=323, step=1)

st.write("TEST - NEW CODE IS RUNNING")
filtered_data = get_region(region, min_magnitude, max_depth)

st.dataframe(filtered_data[["place", "mag", "depth"]].sort_values("mag", ascending=False))

st.map(filtered_data, size=10, color="#4287f5")
st.write("Hello")