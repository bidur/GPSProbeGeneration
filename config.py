
# EDit your Credentials to access Postgis Database  

##-------------Database User Credentials
dbuser		= "postgres"  	# Update with yoour database user name
dbpassword	= "postgres123" # Update with yoour database user passowrd
database  	= "mobility" 	
host		= "localhost"

##------------- local OSM data file OR online
'''
OSM data is accessed online by pyrouteLib3. For local data option 
comment this line and uncomment the following line.
'''
osm_data_source = "" 	
		
#osm_data_source = "pokhara_roads.osm"  # downloaded from OpenStreetMap
#osm data location For offline processing


##------------- Limit Geographic Boundary of Data
# if NOT needed then give empty values
'''
shp_table_name 		= 'gadm36_NPL_2'
column_name			= 'NAME_2'
column_name_value	= 'Bagmati'
'''
shp_table_name 		= ''
column_name			= ''
column_name_value	= ''


## ---- For map-matching input data

target_osm_pbf = 'philippines-latest.osm.pbf' #'nepal-latest.osm.pbf' 'nepal-latest.osm.pbf'#'kyushu-latest.osm.pbf'#

######### DO NOT EDIT BELOW #############

#connect_str = "dbname=mobility user=postgres host='localhost' " + "password='postgres123'"
connect_str = "dbname="+database+" user="+dbuser+" host='"+host+"' " + "password='"+dbpassword+"'"

