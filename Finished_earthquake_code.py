import pandas as pd
import geopandas as gpd
import streamlit as st
import pydeck as pdk
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
st.set_page_config(layout="wide")


st.title("SeismoDex")
st.subheader("Explore global seismic activity through real-time 2026 earthquake data")
st.divider()

url = ("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.csv")
# using the USGS earthquake 2026 dataset
world = gpd.read_file("https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip")
# using GeoPandas to explore a Natural Earth database to visualise the different regions
earthquakes = pd.read_csv(url)

regions = {"Asia": {"min_lat": -10, "max_lat": 90, "min_lon": 25, "max_lon": 180},
           "Europe": {"min_lat": 35, "max_lat": 72, "min_lon": -25, "max_lon": 45},
           "North America": {"min_lat": 7, "max_lat": 83, "min_lon": -170, "max_lon": -50},
           "South America": {"min_lat": -55, "max_lat": 12, "min_lon": -82, "max_lon": -35},
           "Africa": {"min_lat": -34, "max_lat": 39, "min_lon": -17, "max_lon": 50},
           "Antarctica": {"min_lat": -90, "max_lat": -60, "min_lon": -180, "max_lon": 180},
           "Oceania": {"min_lat": -50, "max_lat": 10, "min_lon": 110, "max_lon": 180},
           "World": {"min_lat": -180, "max_lat": 180, "min_lon": -180, "max_lon": 180}}
# define the boundaries of the different areas mapped

if "region" not in st.session_state:
    st.session_state["region"] = "Asia"

st.write("**Choose a region below:**")

st.session_state["region"] = st.pills(
    "Select a region",
    options=regions,
    selection_mode="single",
    default=st.session_state["region"],
    label_visibility="collapsed",
)
# creating buttons for the user to interact with to change the map data

# col5, col6, col7, col8 = st.columns([1, 1, 1.5, 1.5])
# with col5:
#     if st.button("Asia"):
#         st.session_state["region"] = "Asia"
#     if st.button("Africa"):
#         st.session_state["region"] = "Africa"
# with col6:
#     if st.button("Europe"):
#         st.session_state["region"] = "Europe"
#     if st.button("Oceania"):
#         st.session_state["region"] = "Oceania"
# with col7:
#     if st.button("North America"):
#         st.session_state["region"] = "North America"
#     if st.button("Antarctica"):
#         st.session_state["region"] = "Antarctica"
# with col8:
#     if st.button("South America"):
#         st.session_state["region"] = "South America"
#     if st.button("World"):
#         st.session_state["region"] = "World"

region = st.session_state["region"]


def get_region(region, min_magnitude, max_depth):
    if region == "World":
        region_data = earthquakes[
            (earthquakes["mag"] >= min_magnitude) &
            (earthquakes["depth"] <= max_depth)]
        centre_lat = 0
        centre_lon = 0
        zoom = 0.7
    else:
        boundaries = regions[region]
        centre_lat = (boundaries["max_lat"] + boundaries["min_lat"])/2
        centre_lon = (boundaries["max_lon"] + boundaries["min_lon"])/2
        lat_span = boundaries["max_lat"] - boundaries["min_lat"]
        lon_span = boundaries["max_lon"] - boundaries["min_lon"]
        largest_span = max(lat_span, lon_span)
        if largest_span > 160:
            zoom = 0.7
        elif largest_span > 120:
            zoom = 1.7
        elif largest_span > 60:
            zoom = 2
        elif largest_span > 30:
            zoom = 3
        else:
            zoom = 4
        region_data = earthquakes[(earthquakes["latitude"] >= boundaries["min_lat"]) &
                                  (earthquakes["latitude"] <= boundaries["max_lat"]) &
                                  (earthquakes["longitude"] >= boundaries["min_lon"]) &
                                  (earthquakes["longitude"] <= boundaries["max_lon"]) &
                                  (earthquakes["mag"] >= min_magnitude) &
                                  (earthquakes["depth"] <= max_depth)]
    return region_data, centre_lat, centre_lon, zoom

# a function used to define zoom magnitudes and sort region data to isolate the region centre, magnitude and depth


min_magnitude = st.slider("Minimum Magnitude", min_value=2.5, max_value=8.0, value=4.0, step=0.1)
max_depth = st.slider("Maximum Depth", min_value=0, max_value=656, value=323, step=1)
# add info on depth and magnitude

region_data, centre_lat, centre_lon, zoom = get_region(region, min_magnitude, max_depth)


st.subheader("**Seismic Activity Map**")

legend_column, country_column = st.columns([65, 35])

with legend_column:
    st.write("Magnitude: 🟢 2.5–4.0    🟡 4.0–5.5     🟠 5.5–6.5     🔴 6.5+")
    st. caption("Hover over earthquakes for more information")
with country_column:
    if region != "World":
        country = world[world["CONTINENT"] == region]
        country_name = country["NAME"]
        country_selected = st.selectbox("Select a country", country_name)
        selected_country = country[country["NAME"] == country_selected]
        geometry = selected_country.geometry.iloc[0]
        if geometry.geom_type == "MultiPolygon":
            largest_polygon = max(geometry.geoms, key=lambda x: x.area)
            largest_polygon = geometry
            min_lon, min_lat, max_lon, max_lat = largest_polygon.bounds
            centre_lon = (min_lon + max_lon) / 2
            centre_lat = (min_lat + max_lat) / 2
            lat_span = max_lat - min_lat
            lon_span = max_lon - min_lon
            if lon_span > 180:
                centre_lon = 180
                lon_span = 360-lon_span
            largest_span = max(lat_span, lon_span)
            if largest_span > 60:
                zoom = 2
            elif largest_span > 30:
                zoom = 3
            elif largest_span > 15:
                zoom = 4
            elif largest_span > 5:
                zoom = 5
            else:
                zoom = 6


view_state = pdk.ViewState(
    latitude=centre_lat,
    longitude=centre_lon,
    zoom=zoom)


region_data["time"] = pd.to_datetime(
    region_data["time"], utc=True
)

region_data["formatted_time"] = (
    region_data["time"].dt.strftime("%d %B %Y, %H:%M:%S")
)
# time conversion for hover feature

layer = pdk.Layer(
    "ScatterplotLayer",
    data=region_data,
    get_position="[longitude, latitude]",
    get_radius="mag * mag * 3000",
    get_fill_color="mag<4 ? [((mag - 2.5) / 1.5) * 255, 255, 0, 255]: mag<5.5 ? [255, 255 - (((mag - 4.0) / 1.5) * 115), 0, 255]: [255, 140 - (((mag - 5.5) / 2.5) * 140), 0, 255]",
    pickable=True)


map = pdk.Deck(
    layers=layer,
    initial_view_state=view_state,
    tooltip={
        "html": """
            <b>Place:</b> {place}<br/>
            <b>Magnitude:</b> {mag}<br/>
            <b>Depth:</b> {depth} km<br/>
            <b>Time:</b> {formatted_time}
        """,
        "style": {
            "backgroundColor": "#27313D",
            "color": "white",
            "fontSize": "14px",
            "padding": "10px"
        }
    },
    map_style="light"
)
# hov# hover feature for earthquake info

st.markdown("""
<style>
div[data-testid="stDeckGlJsonChart"] {
    overflow: visible !important;
}
</style>
""", unsafe_allow_html=True)

st.pydeck_chart(map, height=600)

st.subheader(f"Earthquake Statistics - {region}")


if not region_data.empty:

    # Calculate earthquake statistics
    num_earthquakes = len(region_data)
    strong_earthquake = region_data["mag"].max()
    ave_mag = region_data["mag"].mean()
    deep_earthquake = region_data["depth"].max()

    # Display statistics in four columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Earthquakes", num_earthquakes)

    with col2:
        st.metric("Strongest", f"M{strong_earthquake:.1f}")

    with col3:
        st.metric("Average Magnitude", f"{ave_mag:.2f}")

    with col4:
        st.metric("Deepest", f"{deep_earthquake:.2f} km")

    st.write("")
    st.subheader("Earthquake Analysis")

    # Consistent styling for all three graphs
    chart_template = "plotly_white"

    chart_font = {
        "family": "Arial",
        "size": 13,
        "color": "#263445"
    }

    chart_layout = {
        "template": chart_template,
        "font": chart_font,
        "paper_bgcolor": "#FFFFFF",
        "plot_bgcolor": "#FFFFFF",
        "margin": dict(l=15, r=15, t=65, b=20),
        "height": 380
    }

    chart_colour = "#168C9B"

    # GRAPH 1: Earthquake magnitude distribution

    magnitude_category = pd.cut(
        region_data["mag"],
        bins=[2.5, 4.0, 5.5, 6.5, 8.0],
        labels=["2.5–4.0", "4.0–5.5", "5.5–6.5", "6.5+"],
        include_lowest=True
    )

    magnitude_counts = (
        magnitude_category.value_counts()
        .reindex(
            ["2.5–4.0", "4.0–5.5", "5.5–6.5", "6.5+"],
            fill_value=0
        )
    )

    # Put magnitude and depth graphs side by side
    graph_col1, graph_col2 = st.columns(2)

    with graph_col1:

        fig = px.bar(
            x=magnitude_counts.index.astype(str),
            y=magnitude_counts.values,
            labels={
                "x": "Magnitude",
                "y": "Number of earthquakes"
            },
            title=f"Magnitude Distribution — {region}",
            color_discrete_sequence=[chart_colour]
        )

        fig.update_layout(
            **chart_layout,
            showlegend=False,
            title=dict(text=f"Magnitude Distribution — {region}", x=0.02)
        )

        fig.update_traces(
            marker_line_width=0,
            hovertemplate=(
                "Magnitude: %{x}<br>"
                "Earthquakes: %{y}"
                "<extra></extra>"
            )
        )

        fig.update_yaxes(
            rangemode="tozero",
            showgrid=True,
            gridcolor="#E8EDF2",
            zeroline=False
        )

        fig.update_xaxes(showgrid=False)

        st.plotly_chart(fig, use_container_width=True)

    # GRAPH 2: Earthquake depth distribution

    with graph_col2:

        fig2 = px.histogram(
            region_data,
            x="depth",
            nbins=20,
            labels={
                "depth": "Depth (km)",
                "count": "Number of earthquakes"
            },
            title=f"Depth Distribution — {region}",
            color_discrete_sequence=[chart_colour]
        )

        fig2.update_layout(
            **chart_layout,
            bargap=0.08,
            title=dict(text=f"Depth Distribution — {region}", x=0.02)
        )

        fig2.update_traces(
            marker_line_width=0,
            hovertemplate=(
                "Depth: %{x}<br>"
                "Earthquakes: %{y}"
                "<extra></extra>"
            )
        )

        fig2.update_yaxes(
            rangemode="tozero",
            showgrid=True,
            gridcolor="#E8EDF2",
            zeroline=False
        )

        fig2.update_xaxes(showgrid=False)

        st.plotly_chart(fig2, use_container_width=True)

    # GRAPH 3: Earthquake frequency over time

    region_data["time"] = pd.to_datetime(
        region_data["time"], utc=True
    )

    daily_counts = (
        region_data["time"]
        .dt.date
        .value_counts()
        .sort_index()
    )

    fig3 = px.line(
        x=daily_counts.index,
        y=daily_counts.values,
        labels={
            "x": "Date",
            "y": "Number of earthquakes"
        },
        title=f"Earthquake Frequency Over Time — {region}",
        markers=True
    )

    fig3.update_layout(
        **chart_layout,
        title=dict(
            text=f"Earthquake Frequency Over Time — {region}",
            x=0.02
        )
    )

    fig3.update_traces(
        line=dict(color=chart_colour, width=2.5),
        marker=dict(size=5, color=chart_colour),
        hovertemplate=(
            "Date: %{x|%d %b %Y}<br>"
            "Earthquakes: %{y}"
            "<extra></extra>"
        )
    )

    fig3.update_yaxes(
        rangemode="tozero",
        showgrid=True,
        gridcolor="#E8EDF2",
        zeroline=False
    )

    fig3.update_xaxes(
        showgrid=False,
        tickformat="%d %b",
        nticks=8
    )

    st.plotly_chart(fig3, use_container_width=True)

else:
    st.write("**There are no earthquakes that match these conditions.**")
st.subheader("Raw Data")
with st.expander("View earthquake data"):
    st.dataframe(
        region_data[["place", "mag", "depth"]]
        .sort_values("mag", ascending=False))

st.caption("All data displayed was taken from the USGS 2026 earthquake feed (Last updated 2026)")

# ADD COMMENTS!!
