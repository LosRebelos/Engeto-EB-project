from sqlalchemy import create_engine
import geopy.distance as gd
import pandas as pd
import pymysql
import streamlit as st
import pydeck as pdk

engine = create_engine("mysql+pymysql://data-student:u9AB6hWGsNkNcRDm@data.engeto.com:3306/data_academy_04_2022")
df_bikes = pd.read_sql(sql=
'''SELECT
	start_station_name,
	start_station_latitude as lat,
	start_station_longitude as lon
FROM edinburgh_bikes eb
GROUP BY start_station_name
ORDER BY COUNT(*) DESC;'''
, con=engine)

st.pydeck_chart(
    pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude= 55.95233546161639,
            longitude= -3.207101172107286,
            zoom=10,
            pitch=50
        ),
        layers = [
            pdk.Layer(
                "ScatterplotLayer",
                df_bikes,
                get_position=['lon', 'lat'],
                get_fill_color=['r', 'g', 'b'],
                get_line_color=[124, 252, 0],
                get_radius= 50
            )
        ]
    )
)
