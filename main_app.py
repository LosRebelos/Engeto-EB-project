from sqlalchemy import create_engine
import geopy.distance as gd
import pandas as pd
import pymysql
import streamlit as st

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

st.map(df_bikes)
