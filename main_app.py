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
page = st.sidebar.radio('Select page', ['About', 'Station activity','The most frequented station'])

if page == 'About':
	st.header('Project author: Pepa Poskočil')

if page == 'Station activity':
	st.header('Shared bikes in Endiburg')
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
if page == 'The most frequented station':
	st.header('The most frequented station')
	limit = st.slider('Count', min_value=5, max_value=30, value=5)
	querry_frequency = '''WITH base AS (
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
						LIMIT {};'''.format(limit)
	df_bikes_frequency = pd.read_sql(sql=querry_frequency, con=engine)
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
					df_bikes_frequency,
					pickable=True,
					auto_highlight=True,
					opacity=0.8,
					stroked=True,
					filled=True,
					get_position=['lon', 'lat'],
					get_fill_color=[255, 128, 0],
					get_radius=50
				),
			]
		)
	)