from sqlalchemy import create_engine
import geopy.distance as gd
import pandas as pd
import pymysql
import streamlit as st
import pydeck as pdk

engine = create_engine("mysql+pymysql://data-student:u9AB6hWGsNkNcRDm@data.engeto.com:3306/data_academy_04_2022")
df_bikes_active = pd.read_sql(sql=
'''WITH base AS (
	SELECT
		start_station_name,
		start_station_latitude as lat,
		start_station_longitude as lon,
		COUNT(*) AS number_of_rents
	FROM edinburgh_bikes eb
	GROUP BY start_station_name
)
SELECT
	start_station_name,
	lat,
	lon,
	number_of_rents
FROM base
WHERE number_of_rents > 200;'''
, con=engine)

df_bikes_noactive = pd.read_sql(sql=
'''WITH base AS (
	SELECT
		start_station_name,
		start_station_latitude as lat,
		start_station_longitude as lon,
		COUNT(*) AS number_of_rents
	FROM edinburgh_bikes eb
	GROUP BY start_station_name
)
SELECT
	start_station_name,
	lat,
	lon,
	number_of_rents
FROM base
WHERE number_of_rents <= 200;'''
, con=engine)

st.set_page_config(layout="wide")
st.title('Edinburgh bikes project')

page = st.sidebar.radio('Select page', ['Mapa','Next','Covid'])

def usage_map():
	if page == 'Mapa':
		st.header('Mapa používání sdílenych kol v Edinburgu')

		st.pydeck_chart(
			pdk.Deck(
				map_style='mapbox://styles/mapbox/light-v9',
				initial_view_state=pdk.ViewState(
					latitude=55.9533,
					longitude=-3.1883,
					zoom=12,
					pitch=50
				),
				layers = [
					pdk.Layer(
						"ScatterplotLayer",
						df_bikes_active,
						get_position=['lon', 'lat'],
						get_fill_color=[124, 252, 0, 160],
						get_line_color=[124, 252, 0, 160],
						get_radius=30
					),
					pdk.Layer(
						"ScatterplotLayer",
						df_bikes_noactive,
						get_position=['lon', 'lat'],
						get_fill_color=[255, 0, 0, 160],
						get_line_color=[255, 0, 0, 160],
						get_radius=30
					),
					]
			)
		)
usage_map()


