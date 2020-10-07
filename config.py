
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


INPUT_SHP_FILE 		= 'gadm36_NPL_shp/gadm36_NPL_2.shp' # keep this empty if your shapefile is already uploaded
shp_table_name 		= 'gadm36_NPL_2'
column_name			= 'NAME_2'
column_name_value	= 'Bagmati'
'''
INPUT_SHP_FILE = ''
shp_table_name 		= ''
column_name			= ''
column_name_value	= ''
'''

## ---- For map-matching input data

target_osm_pbf = 'nepal-latest.osm.pbf' #'philippines-latest.osm.pbf' #'nepal-latest.osm.pbf' #'kyushu-latest.osm.pbf'#

######### DO NOT EDIT BELOW #############

#connect_str = "dbname=mobility user=postgres host='localhost' " + "password='postgres123'"
connect_str = "dbname="+database+" user="+dbuser+" host='"+host+"' " + "password='"+dbpassword+"'"


######## These are moved from main_program.py
TEMP_DIR 		= './output/temp_csv/'
OUTPUT_DIR 		= './output/'
INPUT_DIR 		= './input/'

RAW_CSV_FILE = 'gps_probe_Nepal.csv'
ANONYMIZED_CSV_FILE	= INPUT_DIR +'original_anonymized.csv'

PREPROCESSED_CSV_FILE 	= INPUT_DIR+'preprocessed.csv'	
PREPROCESSED_CLIP_FILE  = INPUT_DIR+'preprocessed_clipped.csv'
SAMPLING_PERCENT = 100 # default

#-------- Database Table names
PROBE_TABLE_NAME  	= 'gps_probe'
CLIPPED_PROBE_TABLE = 'gps_probe_clip'
# graphhopper Map-matching
GPX_DIR = 'map-matching-master/matching-web/src/test/resources/target/'
CSV_DIR = 'input/csv/'
RES_CSV_DIR = 'output/res_csv/' # resultant of mapmatching
