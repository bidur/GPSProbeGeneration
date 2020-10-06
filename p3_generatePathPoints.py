
from pyroutelib3 import Router
#from annomize import anonymize_column_values
#import shapely.wkt
#from shapely.ops import nearest_points
from shapely.geometry import Point
import pandas as pd
import os
#sh
import glob,sys
from datetime import datetime
from config import osm_data_source
#from memprof import *
import shutil
import platform
#platform.system() # 'Windows' , 'Linux'


TEMP_DIR 	= './output/temp_csv/'
OUTPUT_DIR 	= './output/'


def check_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def remove_dir(path):
	if  os.path.exists(path):
		 #os.system("rm -rf "+path)
		 shutil.rmtree(path)


def reomve_temp_files():
	os.chdir(TEMP_DIR)
	files=glob.glob('*.csv')
	for filename in files:
		os.unlink(filename)
		


def get_memory_usage():		
		
	memory_usage = 'NA' # for Windows syste returns 'NA'
	if platform.system() == 'Linux':	
		
	#if  not hasattr(sys, 'getwindowsversion'): # For Linux, Not for windoes OS		
		import sh
		memory_usage = float(sh.awk(sh.ps('u','-p',os.getpid()),'{sum=sum+$6}; END {print sum/1024}')) # MB	
		#print ( 'PLATFORM:   ', platform.system() , memory_usage)

	return memory_usage
	
		
def save_data_2_csv(arr_generated_points, ap_id):
     
    check_dir(TEMP_DIR)    
    df_ap_route = pd.DataFrame(arr_generated_points)    
    df_ap_route = df_ap_route.drop_duplicates()
    
    ap_data_csv = TEMP_DIR + str(ap_id)+ ".csv"
    df_ap_route.to_csv(ap_data_csv,index=False)
    
     		
		
def merge_and_anonymize_csv(final_anonymized_csv):
	## merge all files in TEMP_DIR and save in OUTPUT_DIR
	
	combined_file = OUTPUT_DIR +'combined_csv.csv'  
	
	all_filenames = [i for i in glob.glob(TEMP_DIR+'*.{}'.format('csv'))] # get all csv files
	#print ('all_filenames', all_filenames)
	if (not len(all_filenames)):
		print ('NO Output')
		return
		
	
	#combine all files in the list
	combined_csv = pd.concat([pd.read_csv(f) for f in all_filenames ],sort=True)
	#export to csv
	combined_csv.to_csv(combined_file,index=False) 
	
	#anonymize_column_values( 'ap_id', combined_file, final_anonymized_csv)
	shutil.copy(combined_file,final_anonymized_csv)
	print ('FINAL Output: ', final_anonymized_csv)
	#print ("Final output: %s"% anonymized_csv)
	
	#  remove temp files
	#remove_dir(TEMP_DIR)
	

# for memory profiling use the <@memprof> just before the function
#@memprof(plot = True)
def generate_route_main (ap_id,ts1, ts2, lat1,lon1, lat2, lon2, transport_mode, current_route):
	
	start_time = datetime.now()# start time

		
	'''
	lat2 =  26.65317
	lon2 =  128.090794
	lat1 =  26.66539
	lon1 =  128.103902
	'''	
	#print ap_id,ts1, ts2, lat1,lon1, lat2, lon2, transport_mode, current_route
	
	arr_generated_rows = []
	
	router = None
	if (osm_data_source!=''):
		router = Router(transport_mode,osm_data_source) # use local osm data
	else:
		router = Router(transport_mode) # use osm data from Internet
		

	start = router.findNode(lat1, lon1) # Find start and end nodes
	end = router.findNode(lat2, lon2)


	status = None
	route = None
	
	try:
		#result, route = router.doRoute(node1, node2)
		status, route = router.doRoute(start, end) # Find the route - a list of OSM nodes
	except:
		print('XML parse error:',current_route)
		return []
		# ill formated osm gives errors like Unclosed Token Error is raised by the XML ETree parser, not by pyroutelib.
	
	
	
	n_points = len(route)	
	ts_interval = (ts2 - ts1)/(n_points -1)
	
	if status == 'success':
		routeLatLons = list(map(router.nodeLatLon, route)) # Get actual route coordinates
		

		counter = 0
		for (lat,lon) in routeLatLons:
			
			ts = ts1 + ts_interval * counter 
			#node = data.rnodes[node_id]
			print_line = ("%s,%f,%f,%s" % (ap_id,lat,lon,ts))
			counter += 1
			
			arr_generated_rows.insert(0, {'ap_id': ap_id,  'timestamp':ts, 'latitude': lat, 'longitude':lon})
			
		print ("points count:", counter)

			
	else:
		print (("\t (%s)" % status) ,current_route,	' Skipping...')
		msg = '\n %s %f,%f,%s,%f,%f,%s,--%s--' % (current_route, lat1,lon1,ts1, lat2,lon2,ts2, status )
		log_error(msg) 

		
	#log the time and memory consumed for current transaction
	
	current_memory_mb =  get_memory_usage()
	end_time =  datetime.now() 
	time_taken = (end_time - start_time).total_seconds()
	

	time_msg = '\n'+ current_route +','+   str(len(arr_generated_rows)) +','+ status +','+ str(current_memory_mb) +','+ str(time_taken)+','+ str(start_time) +','+ str( end_time)  
	#print (current_memory_mb, time_msg)
	log_error(msg=time_msg, log_file="log_txn_time.txt")
	
	return arr_generated_rows # number of points got
#####################

def get_timestamp_from_str(ts_str):	
	
	if '.' in ts_str: # microsecond present
		ts_str = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S.%f') 
		
	elif 'Z' in ts_str:# 2019-07-01T12:37:25Z

		ts_str = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%SZ') 
		
	else:
		ts_str = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S') 
		
	return ts_str



def generate_points_timestamp_for_single_ap(ap_id, df_single_ap):	

	row_count = len(df_single_ap)
	transport_mode = 'car'
	arr_generated_points = []
	#ap_id = ''
	log_error() #
	for i in range(row_count-1):
		
		# Case B satisfies here -> same ap_id on multiple roads
		
		ts1 = df_single_ap.iloc[i].timestamp
		ts2 = df_single_ap.iloc[i+1].timestamp
		#print ('ts1 ', ts1)
		#ts1 = datetime.strptime(ts1, '%Y-%m-%d %H:%M:%S.%f') 
		#ts2 = datetime.strptime(ts2, '%Y-%m-%d %H:%M:%S.%f')
		ts1 = get_timestamp_from_str(ts1)
		ts2 = get_timestamp_from_str(ts2)
		
		lat1 = df_single_ap.iloc[i].latitude
		lon1 = df_single_ap.iloc[i].longitude
		geom1 = Point(lat1,lon1)
		
		lat2 = df_single_ap.iloc[i+1].latitude # lat,lon pair may not be on ROAD
		lon2 = df_single_ap.iloc[i+1].longitude   
		geom2 = Point(lat2,lon2)

		#ap_id = df_single_ap.iloc[i].ap_id
		oid1 =  df_single_ap.iloc[i].id
		oid2 =  df_single_ap.iloc[i+1].id
		
		current_route =  str(ap_id) +','+ str(oid1)+'-'+  str(oid2) # this var is used for debugging only

		
		print ("%d Processing ...... %s "%(i,current_route))
		
		if lat1 == lat1 and lon1 == lon2:
			#print ("\t\tsame timestamp -> different location. Skip")
			print ('\t(STAYPOINT: same location -> different timestamp.)',current_route ,'  Skipping...' )
			msg = '\n %s, %f,%f,%s,%f,%f,%s, %s' % (current_route, lat1,lon1,ts1, lat2,lon2,ts2 ,'(StayPoint - DIFF Time  same location)')
			log_error(msg, log_file = 'log_stayPoints.txt')
			
			arr_generated_points.insert(0, {'ap_id': ap_id,  'timestamp':ts1, 'latitude': lat1, 'longitude':lon1})
			arr_generated_points.insert(0, {'ap_id': ap_id,  'timestamp':ts2, 'latitude': lat2, 'longitude':lon2})
			continue
			
		
		
		if (geom1.distance(geom2) > 0): # zero value  means dont skip any 
			# check if the geom1 and geom2 are distant enough  for interpolating points
			
			rows_got  = generate_route_main(ap_id, ts1, ts2, lat1,lon1, lat2,lon2, transport_mode, current_route)
		 
			if len(rows_got):				
				# print current_route, len(rows_got)
				arr_generated_points = arr_generated_points + rows_got
				
			else:
				print ('ParseError!!!')
				#msg = '(ParseError)',  lat1,lon1,ts1, lat2,lon2,ts2, current_route, '  NOT created'
				msg = '\n %s, %f,%f,%s,%f,%f,%s, %s' % (current_route, lat1,lon1,ts1, lat2,lon2,ts2 ,'(ParseError)')
				log_error(msg)
				continue
		  
			
		else:
			# Avoid very near points
			# because near points gets same osm_node id and cant generate points 
			
			print ('\t(same node)',current_route,'  Skipping...')
			#msg = '(same OSM node)',  lat1,lon1,ts1, lat2,lon2,ts2, current_route, '  NOT created'
			msg = '\n %s, %f,%f,%s,%f,%f,%s, %s' % (current_route, lat1,lon1,ts1, lat2,lon2,ts2 , '(sameOSMnode)')
			log_error(msg)
			# manually add the [second] points
		
	
	if len(arr_generated_points):# save data to csv
		save_data_2_csv(arr_generated_points, ap_id)
	else:
		log_error(msg= '\n'+str(ap_id) +',No ROute Found', log_file="log_noRoute.txt")
		
		
	return len(arr_generated_points) # number of points generated
	
############################

def clean_and_load__probe_data(input_file):
	
	# Cleaning done by preprocess_csv.py
	
	print ("Input for ROuting: "+input_file)
	
	selected_fields = ['id','ap_id','latitude','longitude', 'timestamp']
	df_all = pd.read_csv( input_file , usecols=selected_fields )	
	return df_all
	
def get_processed_ap_id():
	arr_ap_ids = []
	
	if os.path.exists(TEMP_DIR):# if directory exists	
	
		arr_csv_files = glob.glob(TEMP_DIR + '*.csv') # all csv in TEMP_DIR

		for path in arr_csv_files:
			ap_id = path.replace('./output/temp_csv/','').replace('.csv','')
			arr_ap_ids.append(ap_id)
		
	return (arr_ap_ids)
		

   
def log_error(msg='', log_file="log_error.txt"):
    
    f = open(OUTPUT_DIR + log_file,'a+') 
    
    if msg =='':
        msg ='\n\n' #new  ap_id messages separated by newlines
    else:
        msg +=','+ str( datetime.now() ) # add time to error messages
        
    f.write(msg)
    f.close()


def generate_osm_routes_main(input_csv_file,output_file ):
	
	df_clean = clean_and_load__probe_data(input_csv_file)
	df_clean['ap_id'] = df_clean['ap_id'].apply(str) # ap_id are assumed to be string	
	
	# get al the ap_id
	arr_ap_ids = df_clean.ap_id.unique()
	
	arr_done = get_processed_ap_id()# get the ap_id porcessed already
	#print (arr_done)

	for ap_id in arr_ap_ids:
		
		if ap_id in arr_done:# avoid ap_id processed beforehand
			print ('<'+ ap_id +'>')
			continue 
			
		#if ap_id=='AP520519':
		#	continue
				
		
		print ('----------------------%s----------------------------'% ap_id)
		
		df_single_ap = df_clean.query('ap_id =="'+ str(ap_id )+'" ') 
		df_single_ap = df_single_ap.sort_values(by=['timestamp'], ascending=True)	
		
		
		start_time = datetime.now()# start time

		point_count = generate_points_timestamp_for_single_ap(ap_id, df_single_ap)		
		
		end_time =  datetime.now() 
		time_taken = (end_time - start_time).total_seconds()
		time_msg = '\n'+str(ap_id)+','+  str(point_count) +','+ str(time_taken)+','+ str(start_time) +','+ str( datetime.now() )  
		log_error(msg=time_msg, log_file="log_ap_id_time.txt")
		
	
	
	
	# merge all csv files in TEMP_DIR to OUTPUT_DIR
	merge_and_anonymize_csv(output_file )
	
	
	
	











