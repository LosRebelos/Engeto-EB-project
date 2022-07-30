from sqlalchemy import create_engine
import geopy.distance as gd
import pandas as pd
import pymysql
import streamlit as st

engine = create_engine("mysql+pymysql://root:kokos123@localhost:3306/test")
df_bikes = pd.read_sql(sql=
'''SELECT
	start_station_name,
	start_station_latitude,
	start_station_longitude,
	COUNT(*) AS number_of_rents
FROM edinburgh_bikes eb
GROUP BY start_station_name
ORDER BY COUNT(*) DESC;'''
, con=engine)

st.map(df_bikes)
