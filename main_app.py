from sqlalchemy import create_engine
import geopy.distance as gd
import pandas as pd
import pymysql
import streamlit as st
import pydeck as pdk
import math

engine = create_engine('mysql+pymysql://data-student:u9AB6hWGsNkNcRDm@data.engeto.com:3306/data_academy_04_2022')




st.set_page_config(layout="wide")
st.title('Edinburgh bikes project')

page = st.sidebar.radio('Select page', ['Map'])


if page == 'Map':
	st.header('Shared bikes in Endiburg')
	col1, col2, col3 = st.columns(3)

	with col1:
		button1 = st.button('Station activity')

	with col2:
		button2 = st.button('The most frequented station')

	with col3:
		button3 = st.button('Button 3')

	if button1:
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

		df_bikes_inactive = pd.read_sql(sql=
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
	
		st.pydeck_chart(
			pdk.Deck(
				map_style='mapbox://styles/mapbox/light-v9',
				initial_view_state=pdk.ViewState(
					latitude=55.9533,
					longitude=-3.1883,
					zoom=12,
					pitch=50
				),
				tooltip= {'html': 	'{start_station_name} </br>'
									'Number of rentals: {number_of_rents} </br>'
				},
				layers = [
					pdk.Layer(
						'ScatterplotLayer',
						df_bikes_active,
						pickable=True,
						auto_highlight=True,
						opacity=0.8,
						stroked=True,
						filled=True,
						get_position=['lon', 'lat'],
						get_fill_color=[0, 255, 0, 160],
						get_radius=30
					),
					pdk.Layer(
						'ScatterplotLayer',
						df_bikes_inactive,
						pickable=True,
						auto_highlight=True,
						opacity=0.8,
						stroked=True,
						filled=True,
						get_position=['lon', 'lat'],
						get_fill_color=[255, 0, 0, 160],
						get_radius=30
					),
				]
			)
		)
	if button2:
		df_bikes_frequency = pd.read_sql(sql=
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
ORDER BY number_of_rents DESC
LIMIT 10;'''
, con=engine)

		st.pydeck_chart(
			pdk.Deck(
				map_style='mapbox://styles/mapbox/light-v9',
				initial_view_state=pdk.ViewState(
					latitude=55.9533,
					longitude=-3.1883,
					zoom=12,
					pitch=50
				),
				tooltip= {'html': 	'{start_station_name} </br>'
									'Number of rentals: {number_of_rents} </br>'
				},
				layers = [
					pdk.Layer(
						'HexagonLayer',
						df_bikes_frequency,
						get_position=['lon', 'lat'],
						radius=200,
						elevation_scale=4,
						elevation_range=[0, 1000],
						pickable=True,
						auto_highlight=True,
						extruded=True
					)	
				]
			)
		)