from tracemalloc import start
from sqlalchemy import create_engine
import pandas as pd
import pymysql
import streamlit as st
import pydeck as pdk
import math
import geopy.distance as gd


# ##################
# Data
# ##################

engine = create_engine('mysql+pymysql://data-student:u9AB6hWGsNkNcRDm@data.engeto.com:3306/data_academy_04_2022')


# ##################
# Vizualizace
# ##################

st.set_page_config(layout="wide")
st.title('Edinburgh bikes project')
page = st.sidebar.radio('Select page', 
									['About', 
									'Station activity',
									'The most frequented station', 
									'Distance between stations'
						])

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
	limit = st.slider('Count for view', min_value=5, max_value=30, value=5)
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

if page == 'Distance between stations':

	q_df_bikes ='''SELECT
		start_station_name,
		start_station_latitude as lat,
		start_station_longitude as lon,
		COUNT(*) AS number_of_rents
	FROM edinburgh_bikes eb
	GROUP BY start_station_name;'''
	df_bikes = pd.read_sql(sql=q_df_bikes, con=engine)
	
	city_choose = st.multiselect('Choose two destiantions', df_bikes['start_station_name'])
	nested_btn = st.button('Search')

	


	if nested_btn is True and len(city_choose) == 2:
		start_des, end_des = city_choose[0], city_choose[1]

		start_lon = df_bikes.loc[df_bikes['start_station_name'] == start_des]['lon'].item()
		start_lat = df_bikes.loc[df_bikes['start_station_name'] == start_des]['lat'].item()

		end_lon = df_bikes.loc[df_bikes['start_station_name'] == end_des]['lon'].item()
		end_lat = df_bikes.loc[df_bikes['start_station_name'] == end_des]['lat'].item()

		distance = round(gd.geodesic((start_lon, start_lat),(end_lon, end_lat)).km, 2)

		st.pydeck_chart(
			pdk.Deck(
				map_style='mapbox://styles/mapbox/light-v9',
				initial_view_state=pdk.ViewState(
					latitude=55.9533,
					longitude=-3.1883,
					zoom=12,
					pitch=50
				),
				tooltip={
					'html': f'{start_des} - {end_des}</br>'
							f'Distance: {distance}km'
				},
				layers = [
					pdk.Layer(
						"LineLayer",
						df_bikes,
						get_source_position= [start_lon, start_lat], 	
						get_target_position= [end_lon, end_lat],		
						get_color= [255, 0, 0],
						get_width=10,
						highlight_color=[255, 255, 0],
						picking_radius=10,
						auto_highlight=True,
						pickable=True
					)
				]
			)
		)
	if nested_btn is True and len(city_choose) != 2:
		st.write('Select two destinations')