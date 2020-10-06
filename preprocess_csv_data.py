
import random 
import pandas as pd
import os, datetime, shutil
# sh,
#from memprof import * # UNCOMMENT for memory Profiling
from p3_generatePathPoints import remove_dir,check_dir
from csv2gpx import  prepare_csv_files, convert_csv2gpx
from gpx2csv import convert_resgpx2csv
#from annomize import anonymize_column_values
from config import target_osm_pbf

MAP_MATCHING_PATH ='map-matching-master/'
GPX_DIR = 'map-matching-master/matching-web/src/test/resources/target/'
CSV_DIR = 'input/csv/'
RES_CSV_DIR = 'output/res_csv/' # resultant of mapmatching
OUTPUT_DIR 	= './output/'

#@memprof(plot = True) # UNCOMMENT for memory Profiling
def preprocess_data(sampling_percent, input_file, output_file):
	
	df = pd.read_csv(input_file)# 4900 rows
	df['ap_id'] = df['ap_id'].apply(str) # ap_id are assumed to be string	

	#remove duplicate rows
	df.drop_duplicates(inplace=True) # 48782rows

	# get duplicate rows in terms of 'ap_id' and 'timestamp'
	df_dup = df[df.duplicated(['ap_id','timestamp'],keep=False)] # 294 rows # 60 ap_id
	df_dup = df_dup.sort_values(by=['ap_id'], ascending=True)

	# remove all duplicates from df -> new values will be calculated and kept for the duplicates
	df_clean = df.drop_duplicates(['ap_id','timestamp'], keep=False)
	
	
	# Handle case: same timestamp and differnt location (e.g. L1 and L2 have same timestamp t1) -> remove these values and keep a single location ( avg(l1,l3), t1)
	arr_clean_rows = []
	arr_ap_id = df_dup.ap_id.unique() # duplicate ap_id

	# process each ap_id
	for ap_id in arr_ap_id:
		#ap_id = 'AP521696' #arr_ap_id[0]
		df_ap_id = df_dup.query('ap_id == "'+str(ap_id)+'"')
		# get duplicate ts for the ap_id
		arr_ts =  df_ap_id.timestamp.unique()
		
		# process each ts
		for ts in arr_ts:
			#ts = arr_ts[0]
			df_ts = df_ap_id[df_ap_id['timestamp'].isin([ts])]
			new_lat = df_ts['latitude'].mean()
			new_lon = df_ts['longitude'].mean()
			arr_clean_rows.append({'ap_id': ap_id,  'timestamp':ts, 'latitude': new_lat, 'longitude':new_lon})

		
	# add new row to clean df
	if len(arr_clean_rows):
		df_clean = df_clean.append(arr_clean_rows)

	
	# APPLY sampling_percent
	df_sample = apply_sampling(sampling_percent, df_clean)
	
	
	
	prepare_csv_files(df_sample,CSV_DIR) # csv2gpx.py
	convert_csv2gpx(CSV_DIR,GPX_DIR)
	
	# Apply graphhopper MapMatching
	#1.prepare map cache
	prepare_map_cache()
	# 2. apply map matching
	apply_map_matching() # match input GPS probe to road network
	# 3. convert result to csv and popuate timestamp based on the input file
	df_mapped_route = convert_resgpx2csv(CSV_DIR, GPX_DIR, RES_CSV_DIR) # Convert road mapped GPS Probe to CSV and update timestamp
	
	# gpx2csv.py -> get a single file
	
	if 'id' not in df_mapped_route.columns:
		df_mapped_route.insert(0,'id',range(len(df_mapped_route)))# add a new id column
		
	df_mapped_route.to_csv(output_file,index=False)
	
	print (output_file)
	shutil.copy(output_file, OUTPUT_DIR + 'final_csv_4_mobmap.csv') # mobmap visualization without using OSM routes from pyRouteLib3
	#anonymize_column_values( 'ap_id', output_file, OUTPUT_DIR+'final_csv_4_mobmap.csv') 

	return None


def apply_map_matching():	
	
	os.chdir(MAP_MATCHING_PATH)
	print("Current Working Directory " , os.getcwd())
	
	input_gpx_files = GPX_DIR.replace(MAP_MATCHING_PATH,'') + '*.gpx'
	create_route_command ='java -jar matching-web/target/graphhopper-map-matching-web-1.0-SNAPSHOT.jar match '+ input_gpx_files	
	os.system(create_route_command)
	print ('\ncompleted: ' ,create_route_command)
	
	os.chdir(os.path.dirname(__file__)) # change dir to  current .py file dir
	
	#print ('MAP dir: ', MAP_MATCHING_PATH)
	#print ('RUnning FILE DIR: ', os.path.dirname(__file__) )
	#print("Current Working Directory " , os.getcwd())
	
	return None
	

def prepare_map_cache():
	
	cache_loc = 'map-matching-master/graph-cache/'
	remove_dir(cache_loc) # remove old cache
	create_map_cache_command ='java -jar matching-web/target/graphhopper-map-matching-web-1.0-SNAPSHOT.jar import map-data/'+target_osm_pbf
	os.chdir(MAP_MATCHING_PATH)
	os.system(create_map_cache_command)
	os.chdir(os.path.dirname(__file__)) # change dir to  current .py file dir
	
	print ('\ncompleted: ' ,create_map_cache_command)
	
	return None
	

def apply_sampling(sampling_percent, df_all):
	
	# lst = lst[:len(lst)-n]
	
	arr_ap_id = df_all.ap_id.unique() # duplicate ap_id
	#print (  len(arr_ap_id))
		
	id_count_to_keep = int(len(arr_ap_id) * sampling_percent * 0.01 ) 
	#arr_ap_id = arr_ap_id[:id_count_to_keep]
	if  id_count_to_keep == 0:
		id_count_to_keep = 1
		
	
	arr_ap_id_sampled = random.sample(list(arr_ap_id), id_count_to_keep)#  to randomly select samples
	#print (  len(arr_ap_id_sampled))
	
	df_sample = df_all[df_all.ap_id.isin(arr_ap_id_sampled)]
	#df[df.ap_id.isin(arr_ap_id)]
	return df_sample
	

	
