from sqlalchemy import create_engine
from sklearn.metrics import DistanceMetric
import geopy.distance as gd
import pandas as pd
import streamlit as st
import pydeck as pdk
import numpy as np
import datetime as dt
import altair as alt
import matplotlib.pyplot as plt

###############
# DATAFRAME
###############

engine = create_engine('mysql+pymysql://data-student:u9AB6hWGsNkNcRDm@data.engeto.com:3306/data_academy_04_2022')
querry ='''SELECT
		*
	FROM edinburgh_bikes eb;'''
df = pd.read_sql(sql=querry, con=engine)

# ##############
# DATA FILTER
# ##############

# ### 1 + 4 ###
# List of stations
def stations():
	q_stations = '''SELECT 
			start_station_name AS station_name,
			start_station_latitude AS lat,
			start_station_longitude AS lon
		FROM edinburgh_bikes eb
		GROUP BY start_station_name
		UNION
		SELECT 
			end_station_name AS station_name,
			end_station_latitude AS lat,
			end_station_longitude AS lon
		FROM edinburgh_bikes eb
		GROUP BY end_station_name;'''
	df_stations = pd.read_sql(sql=q_stations, con=engine)
	df_stations = df_stations.merge(rents_counts(),how='left', left_on='station_name', right_on='station_name')
	df_stations = df_stations.merge(return_counts(),how='left', left_on='station_name', right_on='station_name')
	df_stations = df_stations.fillna(0)
	df_stations['flow'] = df_stations['return_count'] - df_stations['rents_count']
	return df_stations

# ### 2 ###
# Total count of rented bikes
def rents_counts():
	rents = df['start_station_name'].value_counts().reset_index()
	rents.columns = ['station_name', 'rents_count']
	return rents
# Most frequent stations
def top_stations(limit):
	return stations().sort_values(by=['rents_count'], ascending=False)[0:limit]

# ### 3 ###
# Total count of returned bikes
def return_counts():
	returns = df['end_station_name'].value_counts().reset_index()
	returns.columns = ['station_name', 'return_count']
	return returns


# ### 5 ###
# Average time for rent
def avg_rent_duration():
	df_dur = df[['started_at', 'duration']].copy()
	avg_duration = df_dur['duration'].mean()
	return avg_duration

# Average time for rent by months
def month_avg_dur():
	q_avg_dur = '''SELECT
		date_format(started_at, '%%Y %%M') as date,
		AVG(duration) as avg_duration
	FROM edinburgh_bikes eb
	GROUP BY MONTH(started_at), YEAR(started_at);'''
	df_avg_dur = pd.read_sql(sql=q_avg_dur, con=engine)
	return df_avg_dur

# Outlier values for bikes rents
def outlier_dur(value):
	outlier_value = value * avg_rent_duration()
	df_outlier = df[df['duration'] > outlier_value]
	return df_outlier


# ### Demand analysis ###
# Demand trend for rent bikes by month
def month_rents():
	# q_m_rents = '''SELECT 
	# 	date_format(started_at, '%%Y') as Year,
	# 	date_format(started_at, '%%m') as Month,
	# 	count(start_station_name) 
	# FROM edinburgh_bikes eb
	# GROUP BY MONTH(started_at), YEAR(started_at);'''
	# df_m_rents = pd.read_sql(sql=q_m_rents, con=engine)
	# df_m_rents = df_m_rents.rename(columns={'count(start_station_name)': 'Rents count'})
	q_m_rents = '''SELECT
		started_at as date
		FROM edinburgh_bikes eb
		GROUP BY date;'''
	df_m_rents = pd.read_sql(sql=q_m_rents, con=engine)

	df_m_rents['date'] = pd.to_datetime(df_m_rents['date'])
	df_m_rents['date'] = df_m_rents['date'].apply(lambda x: x.strftime('%Y-%m'))
	df_m_rents = df_m_rents.value_counts()
	df_m_rents = df_m_rents.to_frame('count').reset_index()
	df_m_rents = df_m_rents.sort_values(by=['date'])
	return df_m_rents

# identifikujte příčiny výkyvů poptávky + zjistěte vliv počasí na poptávku po kolech
def weather():
	querry_weather = '''SELECT
		*
	FROM edinburgh_weather ew;'''
	df_weather = pd.read_sql(sql=querry_weather, con=engine)

	#Column rename
	df_weather = df_weather.rename(columns={
    'temp': 'temp[°C]',
	'feels': 'feels[°C]', 
    'rain': 'rain[mm]',
    'humidity': 'humidity[%]',
    'cloud': 'cloud[%]'}
    )

	#Column drop
	df_weather = df_weather.drop(columns= [
	'wind',
	'gust',
	'pressure',
	'vis']
	)

	#Change units, change data types
	df_weather['temp[°C]'] = df_weather['temp[°C]'].str.replace(' °c', '').astype('int')
	df_weather['feels[°C]'] = df_weather['feels[°C]'].str.replace(' °c', '').astype('int')
	df_weather['rain[mm]'] = df_weather['rain[mm]'].str.replace(' mm', '').astype('float')
	df_weather['humidity[%]'] = df_weather['humidity[%]'].str.replace('%', '').astype('int')
	df_weather['cloud[%]'] = df_weather['cloud[%]'].str.replace('%', '').astype('int')
	df['date'] = df['started_at'].str.split(' ', expand=True)[0]

	df_weather = (df_weather[['date', 'temp[°C]', 'feels[°C]',  'rain[mm]', 'humidity[%]', 'cloud[%]']]
                           .groupby('date')
                           .mean()
                           .reset_index()
                           .round(2)
                           )

	df_weather = pd.merge(df, df_weather, left_on='date', right_on='date')
	df_month_weather = df_weather.copy()
	df_month_weather['date'] = pd.to_datetime(df_month_weather['date'])
	df_month_weather = df_month_weather.set_index('date')
	df_month_weather = (df_month_weather[['temp[°C]', 'feels[°C]',  'rain[mm]', 'humidity[%]', 'cloud[%]']]
							.groupby(pd.Grouper(freq="M"))
							.mean()
							.reset_index()
							.round(2)
							)
	df_month_weather['date'] = df_month_weather['date'].apply(lambda x: x.strftime('%Y-%m'))
	return df_month_weather

# Do people rent bikes more at the weekend than during the work week?
def weekday():
	df_weekday = df['started_at']
	df_weekday = pd.to_datetime(df_weekday)
	df_weekday = df_weekday.dt.dayofweek
	df_weekday = df_weekday.value_counts()
	df_weekday = df_weekday.rename({0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'})
	df_weekday = df_weekday.to_frame()
	df_weekday.reset_index(inplace=True)
	df_weekday = df_weekday.rename(columns = {'index':'Day', 'started_at': 'Rents count'})
	return df_weekday

# ##############
# VISUALIZATION
# ##############

st.set_page_config(layout="wide")
page = st.sidebar.radio('Select page', 
									['About', 
									'Stations activity',
									'The most frequented station',
									'Bicycle flow', 
									'Distance between stations',
									'How long rent takes',
									'Rents demand',
									'The effect of weather on demand',
									'Weekends or business days?'

						])

if page == 'About':
	st.title('Edinburgh bikes project')
	st.header('Project author: Pepa Poskočil')
	st.image('about_img.jpg')

if page == 'Stations activity':
	st.title('Stations activity')
	st.write('''On this map you can find Active 
	<span style='color: green; font-style: oblique; font-weight: bold'>GREEN</span> 
	and inactive 
	<span style='color: red; font-style: oblique; font-weight: bold'>RED</span> 
	stations.''', 
	unsafe_allow_html=True
	)

	df_stations_active = stations().where(stations()['rents_count'] > 500).dropna()
	df_stations_inactive = stations().where(stations()['rents_count'] <= 500).dropna()

	st.pydeck_chart(
		pdk.Deck(
			map_style='mapbox://styles/mapbox/light-v9',
			initial_view_state=pdk.ViewState(
				latitude=55.9533,
				longitude=-3.1883,
				zoom=12,
				pitch=50
			),
			tooltip= {'html': 	'{station_name} </br>'
								'Number of rentals: {rents_count} </br>'
			},
			layers = [
				pdk.Layer(
					'ScatterplotLayer',
					df_stations_active,
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
					df_stations_inactive,
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
	st.title('The most frequented station')
	limit = st.slider('Count for view', min_value=5, max_value=30, value=5) + 1

	st.pydeck_chart(
		pdk.Deck(
			map_style='mapbox://styles/mapbox/light-v9',
			initial_view_state=pdk.ViewState(
				latitude=55.9533,
				longitude=-3.1883,
				zoom=12,
				pitch=50
			),
			tooltip= {'html': 	'{station_name} </br>'
								'Number of rentals: {rents_count} </br>'
			},
			layers = [
				pdk.Layer(
					'ScatterplotLayer',
					top_stations(limit),
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

if page == 'Bicycle flow':
	st.title('Bicycle flow')
	st.write('''On this map you can find flow of bicykles. 
	<br>Stations marking:</br> 
	<br><span style='color: pink; font-style: oblique; font-weight: bold'>PINK</span> - increase flow (bicycles are piling up)</br> 
	<br><span style='color: purple; font-style: oblique; font-weight: bold'>PURPLE</span> - balance flow</br>
	<br><span style='color: gray; font-style: oblique; font-weight: bold'>GRAY</span> - decrease flow (bicycles are decreasing)</br>
	''', 
	unsafe_allow_html=True
	)

	increase_flow = stations().where(stations()['flow'] > 0).dropna()
	decrease_flow = stations().where(stations()['flow'] < 0).dropna()
	balanced_flow = stations().where(stations()['flow'] == 0).dropna()

	st.pydeck_chart(
		pdk.Deck(
			map_style='mapbox://styles/mapbox/light-v9',
			initial_view_state=pdk.ViewState(
				latitude=55.9533,
				longitude=-3.1883,
				zoom=12,
				pitch=50
			),
			tooltip= {'html': 	'{station_name} </br>'
								'Number of rentals: {rents_count} </br>'
								'Number of returns: {return_count} </br>'
								'Flow: {flow} </br>'
			},
			layers = [
				pdk.Layer(
					'ScatterplotLayer',
					increase_flow,
					pickable=True,
					auto_highlight=True,
					opacity=0.8,
					stroked=True,
					filled=True,
					get_position=['lon', 'lat'],
					get_fill_color=[0, 0, 0, 160],
					get_radius=30
				),
				pdk.Layer(
					'ScatterplotLayer',
					decrease_flow,
					pickable=True,
					auto_highlight=True,
					opacity=0.8,
					stroked=True,
					filled=True,
					get_position=['lon', 'lat'],
					get_fill_color=[251, 37, 118, 160],
					get_radius=30
				),
				pdk.Layer(
					'ScatterplotLayer',
					balanced_flow,
					pickable=True,
					auto_highlight=True,
					opacity=0.8,
					stroked=True,
					filled=True,
					get_position=['lon', 'lat'],
					get_fill_color=[63, 0, 113, 160],
					get_radius=30
				)
			]
		)
	)

	st.write('Or you may find flow in this table')
	st.dataframe(stations())

if page == 'Distance between stations':
	st.title('Distance between station')
	st.header('Distance matrix in metres')

	df_distance_stations = stations()[['station_name', 'lat', 'lon']]
	df_distance_stations['lat'] = np.radians(df_distance_stations['lat'])
	df_distance_stations['lon'] = np.radians(df_distance_stations['lon'])

	distance_metric = DistanceMetric.get_metric('haversine')
	distances = pd.DataFrame(
    	distance_metric.pairwise(
        	df_distance_stations[['lat','lon']])*6373000, #calculation for meters  
            	columns=df_distance_stations.station_name, 
            	index=df_distance_stations.station_name).astype(int)

	distances = distances.loc[:,~distances.columns.duplicated()]
	st.dataframe(distances)

if page == 'How long rent takes':
	st.title('How long rent takes')
	st.write('Average duration of rent: ', round(avg_rent_duration(), 2), 'seconds')

	st.header('Average rent duration per months')
	st.dataframe(month_avg_dur())

	st.header('Outlier values of duration')
	value = st.slider('Use slider to manage multiple of average duration to show outlier values', min_value=10, max_value=50, value=5)
	st.dataframe(outlier_dur(value))

if page == 'Rents demand':
	st.title('Rents demand')

	bar_chart = alt.Chart(month_rents()).mark_bar().encode(
		alt.X('date'),
		alt.Y('count'),
		tooltip=['date', 'count']
	)
	st.altair_chart(bar_chart, use_container_width=True)

if page == 'The effect of weather on demand':
	st.title('The effect of weather on demand')
	st.header('Average value')

	col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 3])

	temp_val = str(int(weather()['temp[°C]'].mean().round(0))) + ' °C'
	col1.metric('Temperature', temp_val)

	feels_val = str(int(weather()['feels[°C]'].mean().round(0))) + ' °C'
	col2.metric('Feels temperature', feels_val)

	rain_val = str(weather()['rain[mm]'].mean().round(2)) + ' mm'
	col3.metric('Rain', rain_val)

	hum_val = str(int(weather()['humidity[%]'].mean().round(0))) + ' %'
	col4.metric('Humidity', hum_val)

	cloud_val = str(int(weather()['cloud[%]'].mean().round(0))) + ' %'
	col5.metric('Cloud', cloud_val)

	st.write('Moje povídání')

	fig, axes = plt.subplots(5, 1, figsize=(20, 15))
	plt.subplots_adjust(hspace = .01)

	weather().plot('date', 'temp[°C]', ax=axes[0], 
					color='blue', 
					label='temperature [°C]')
	weather().plot('date', 'feels[°C]', ax=axes[0], 
					color='orange', 
					label='Feels temperature [°C]')

	weather().plot.bar('date', 'rain[mm]', ax=axes[1], 
						ylabel='rain [mm]', 
						label='rain [mm]')
	
	weather().plot('date', 'humidity[%]', ax=axes[2], 
					color='blue', 
					label='humidity [%]', 
					ylabel='humidity [%]')

	weather().plot('date', 'cloud[%]', ax=axes[3], 
					color='blue', 
					label='Cloud [%]', 
					ylabel='Cloud [%]')

	month_rents().plot.bar('date', 'count', ax=axes[4],
						ylabel='Number of rents', 
						label='Number of rents')

	st.pyplot(fig)

if page == 'Weekends or business days?':
	st.title('Weekends or business days?')
	st.header('Rents over days')

	bar_chart = alt.Chart(weekday()).mark_bar().encode(
		alt.X('Day', sort=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']),
		alt.Y('Rents count'),
		tooltip=['Day', 'Rents count']
	)
	st.altair_chart(bar_chart, use_container_width=True)

