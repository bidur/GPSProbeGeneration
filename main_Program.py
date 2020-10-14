# https://www.codermantra.com/entry-tkinter/
from datetime import datetime

import psycopg2 
import sys,os,shutil
from p3_generatePathPoints import remove_dir,check_dir,generate_osm_routes_main, log_error
from preprocess_csv_data import preprocess_data
#from  csv_insert_DB import csv_2_db # slower than COPY command
import pandas as pd
from tkinter import *
from tkinter import filedialog
import time


#config.py contains Variables that contains the user credentials to access Twitter API 
from config import connect_str,dbpassword,dbuser,host,database,shp_table_name,column_name,column_name_value
from config import TEMP_DIR,OUTPUT_DIR,INPUT_DIR,ANONYMIZED_CSV_FILE,INPUT_SHP_FILE,PREPROCESSED_CSV_FILE,PREPROCESSED_CLIP_FILE, SAMPLING_PERCENT
from config import PROBE_TABLE_NAME,CLIPPED_PROBE_TABLE, GPX_DIR, CSV_DIR, RES_CSV_DIR, RAW_CSV_FILE

#######
warning_color 	= 'red'
success_color 	= 'cyan'
misc_color 		= 'azure'
head_color 	= 'thistle1'
'''
########
TEMP_DIR 		= './output/temp_csv/'
OUTPUT_DIR 		= './output/'
INPUT_DIR 		= './input/'
ANONYMIZED_CSV_FILE	= INPUT_DIR +'original_anonymized.csv'
INPUT_SHP_FILE = ''
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
'''
#--------functions
  
def close_connection(connection):
    
    if connection is not None:
        connection.close()
        print('Connection closed.')


def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:      
        # connect to the PostgreSQL server
        print('\n Database connected...')
        conn = psycopg2.connect(connect_str)
   
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
   
    return conn


def clip_points_within_selected_region(clean_table_name):
	
	drop_table(clean_table_name)# drop table if exists  
	

	print ("\n Clipping Points within selected Region  \n\t Please wait...")
	#sql = " create table "+ clean_table_name +" AS	SELECT o.*	FROM "+PROBE_TABLE_NAME+" o ,"+shp_table_name+" a WHERE ST_DWithin(a.geom::geography, o.geom::geography, 0.01 ) and  a."+column_name+"='"+column_name_value+"';"
	
	sql = "	CREATE TABLE "+ clean_table_name +" AS	SELECT o.*	FROM "+PROBE_TABLE_NAME+" o ,"+shp_table_name+" a WHERE ST_DWithin(a.geom, o.geom, 0.01 ) AND  a."+column_name+"='"+column_name_value+"';"
	
 
	
	print (sql)
	
	conn= connect()
	cur = conn.cursor()
	cur.execute(sql)  
	conn.commit()	 
	cur.close()
	close_connection(conn)
	
	
  
def drop_table(table_name):     
	conn= connect()
	cur = conn.cursor()
	conn.autocommit = True
	drop_sql = "DROP TABLE IF EXISTS "+ table_name
	print (drop_sql)
	cur.execute(drop_sql) 	
	cur.close()
	close_connection(conn)
	
	time.sleep(2) # sleep for 2 seconds
      
      
def create_db_table(table_name):
	#1. remove table if exists, 2. add csv to table, 3.create geom field
	
	
	drop_table(table_name)# drop table if exists
	
	conn= connect()
	cur = conn.cursor()
		
	create_sql = "CREATE TABLE "+ table_name + "	(\
			id integer,\
			ap_id text ,\
			timestamp timestamp without time zone,\
			latitude double precision,\
			longitude double precision,\
			geom geometry(Point,4326)\
		)"
		
	print (create_sql)
	print ("_________________________________________________________")
		
	cur.execute(create_sql) 
	conn.commit()
	
	cur.close()
	close_connection(conn)
	
	
def create_geometry_from_latlon(table_name):
	conn= connect()
	cur = conn.cursor()
	update_sql = "UPDATE "+ table_name +" SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);"
	
	print (update_sql)
	print ("_________________________________________________________")
	cur.execute(update_sql)  # executemany
	conn.commit()
	
	cur.close()
	close_connection(conn)



def create_spatial_index(table_name):
	conn= connect()
	cur = conn.cursor() #
	conn.autocommit = True
	sql = "CREATE INDEX ON "+ table_name +" USING GIST(geom);"
	
	print (sql)
	print ("_________________________________________________________")
	cur.execute(sql)  # executemany
	#conn.commit()
	
	cur.close()
	close_connection(conn)



def vaccum_analyze_spatial_index(table_name):
	conn= connect()
	cur = conn.cursor() #
	conn.autocommit = True
	sql = "VACUUM ANALYZE "+ table_name +";"
	
	print (sql)
	print ("_________________________________________________________")
	cur.execute(sql)  # executemany
	#conn.commit()
	
	cur.close()
	close_connection(conn)


def transform_epsg(table_name, col = 'geom', geometry ='Point', epsg=4326):
	conn= connect()
	cur = conn.cursor() #
	conn.autocommit = True
	sql =  "ALTER TABLE "+ table_name +" \
			ALTER COLUMN "+col+" \
			TYPE Geometry("+geometry+", "+str(epsg)+")  USING ST_Transform(geom, "+str(epsg)+");"
	
	print (sql)
	print ("_________________________________________________________")
	cur.execute(sql)  # executemany
	#conn.commit()
	
	cur.close()
	close_connection(conn)



def clip_data_for_selected_region():
	#--- 2.import csv to PostGIS	
	create_db_table(PROBE_TABLE_NAME)# create target table , drop existing table with same name
	csv_2_psql(PREPROCESSED_CSV_FILE, PROBE_TABLE_NAME)
	
	create_geometry_from_latlon(PROBE_TABLE_NAME)
	
	### CREATE INDEX on Geometry column	
	create_spatial_index(PROBE_TABLE_NAME)
	vaccum_analyze_spatial_index(PROBE_TABLE_NAME)
	
	
	## convert to planner projection ( for faster join operation)
	transform_epsg(PROBE_TABLE_NAME, col = 'geom' , geometry= 'Point', epsg=3857)
	
	transform_epsg(shp_table_name, col = 'geom', geometry= 'MultiPolygon', epsg=3857)

	### Create spatial index for shp table and probe table
	start_time =  datetime.now()
	print (start_time)
	
	#--- 3. Clip GPS points within original region	
	clip_points_within_selected_region(CLIPPED_PROBE_TABLE) ### UNCOMMENT
	
	end_time =  datetime.now() 
	time_taken = (end_time - start_time).total_seconds()
	
	log_error('clip_points_within_selected_region() time(sec) '+ str(time_taken), log_file = 'log_DatabaseTime.txt')
	
	
	#--- 4.  save clean_clipped data to csv
	transform_epsg(PROBE_TABLE_NAME, col = 'geom' , geometry= 'Point', epsg=4326)

	psql_2_csv(PREPROCESSED_CLIP_FILE, CLIPPED_PROBE_TABLE)
	
	
def csv_2_psql(csv_file_name, table_name):	
		
	conn = connect()
	cur = conn.cursor()
	conn.autocommit = True
	csv_fr = open(csv_file_name, 'r') 
	cols = csv_fr.readline().strip('\n').split(',')
	cur.copy_from(csv_fr, table_name, sep=',', columns= cols)  
	csv_fr.close()
	cur.close()
	close_connection(conn)
	print("Imported Data from ", csv_file_name, ' to ', table_name)
	print ("_________________________________________________________")
	
	

def psql_2_csv(csv_file_name, table_name):
	
	conn = connect()
	sql_query = "SELECT *  FROM "+ table_name
	df_original = pd.read_sql_query(sql = sql_query, con = conn)
	close_connection(conn)
	df_original.to_csv(csv_file_name,index=False)
	print("Preprocessed and CLipped File saved: ", csv_file_name)
	print ("_________________________________________________________")
			

def preprocess_csv_file():
	
	if not os.path.isfile(ANONYMIZED_CSV_FILE):# if directory exists	
		print("NOT available: ", ANONYMIZED_CSV_FILE)
		lbl_preprocess.config(bg=warning_color)  
		lbl_preprocess["text"] = " Make sure 'original.csv' \n is copied to 'input/' dir " 
		return
		
	SAMPLING_PERCENT =  int (svar_sample.get() )
	
	
	#---1. preprocess : deduplicate rows, handle ( same ts, diff loc)
	preprocess_data(SAMPLING_PERCENT, ANONYMIZED_CSV_FILE,  PREPROCESSED_CSV_FILE)
	
	if shp_table_name != '':
		clip_data_for_selected_region()

	lbl_preprocess.config(bg=success_color)
	lbl_preprocess["text"] = " Preprocessing Complete"


def preprocessing_completed(preprocessed_file_name):
	
	if not os.path.isfile(preprocessed_file_name):
		lbl_generate_routes.config(bg=warning_color)
		lbl_generate_routes["text"] = "Please Complete Preprocessing FIRST !"
		
		return False
	
	return True
	
def generate_routes():
		
	#PREPROCESSED_CLIP_FILE
	output_file =  OUTPUT_DIR +"final_csv_4_mobmap_big.csv"
	if shp_table_name == '':
		if preprocessing_completed(PREPROCESSED_CSV_FILE):
			generate_osm_routes_main(PREPROCESSED_CSV_FILE,output_file)		
	else:
		if preprocessing_completed(PREPROCESSED_CLIP_FILE):
			generate_osm_routes_main(PREPROCESSED_CLIP_FILE,output_file)
		
	lbl_generate_routes.config(bg=success_color)
	lbl_generate_routes["text"] = " Route Generation Complete. Check " + OUTPUT_DIR

from annomize import anonymize_column_values

      
def select_csv_file():
	
	input_file = filedialog.askopenfilename()
	filename, file_extension = os.path.splitext(input_file)
	command =''
	if file_extension == '.csv':
		#shutil.copy(input_file,ANONYMIZED_CSV_FILE)
		df = pd.read_csv(input_file) # pandas can deal with encodings
		input_file_temp = INPUT_DIR+'input_file_temp.csv'
		df.to_csv(input_file_temp,index=False)
		df.to_csv(input_file_temp,index=False)
		anonymize_column_values( 'ap_id', input_file_temp, ANONYMIZED_CSV_FILE)
		
		lbl_csv_file.config(bg=success_color) 
		lbl_csv_file["text"] = " CSV file location saved "  
	
	else:
		lbl_csv_file.config(bg=warning_color)  
		lbl_csv_file["text"] = " Please select proper csv file " 
	
	print ('File Obtained: ',input_file)
	print ("_________________________________________________________")

################

def select_shp_file():
	
	INPUT_SHP_FILE = filedialog.askopenfilename()
	
	print (INPUT_SHP_FILE)
	

	filename, file_extension = os.path.splitext(INPUT_SHP_FILE)
	if file_extension == '.shp':
		drop_table(shp_table_name)# drop table if exists  
		create_table_command = 'shp2pgsql -I -s 4326 '+INPUT_SHP_FILE+'  '+ shp_table_name +' | PGPASSWORD='+dbpassword+' psql -d '+database+' -h '+host+' -U '+dbuser+' '
		print (create_table_command)
		print ("_________________________________________________________")
		os.system(create_table_command)
		
		lbl_shp.config(bg=success_color) 
		lbl_shp["text"] = " Shapefile imported to PostGIS "  
	
	else:
		lbl_shp.config(bg=warning_color)  
		lbl_shp["text"] = " Please select proper Shapefile " 
   
########

def get_sampling_percent(cur):         #<-- function to run
    SAMPLING_PERCENT = cur           #<-- 'cur' is the selected value
 
 
 
	    		
#################################################    

# remove old files
remove_dir(OUTPUT_DIR)
remove_dir(INPUT_DIR)
remove_dir(GPX_DIR)
remove_dir(CSV_DIR)
remove_dir(RES_CSV_DIR)


# create necessary directories
check_dir(INPUT_DIR)
check_dir(OUTPUT_DIR)
check_dir(TEMP_DIR)
check_dir(GPX_DIR)
check_dir(CSV_DIR)
check_dir(RES_CSV_DIR)
	
win=Tk()
win.geometry('800x560')
win.title(' GPS Probe Mobility Analysis ')
	
lbl_title=Label(win,text="GPS Probe Mobility Analysis",  background='cyan',font=('Helvetica', 24, 'bold'))
lbl_title.grid(row=0,column=1)
lbl_title.config(bg=head_color,fg="blue")  


l0=Label(win,text="                                ")
l0.grid(row=1,column=0)
l00=Label(win,text="_____________________________")
l00.grid(row=1,column=1)

lbl_csv2=Label(win,text="0. Select SHP Files",font=('Helvetica', 18, 'bold'))
lbl_csv2.config(bg=head_color)  
lbl_csv2.grid(row=2,column=1)

btn_shp = Button(win, text="Select SHP File", command=select_shp_file)
btn_shp.grid( row=3, column=1)

lbl_shp=Label(win,text='')
lbl_shp.grid(row=3,column=2)

lbl_shp_opt=Label(win,text="OPTIONAL",font=('Helvetica', 10, 'bold'))
lbl_shp_opt.config(bg=misc_color)  
lbl_shp_opt.grid(row=3,column=0)

l2=Label(win,text="shp2pgsql NOT in system path then \n Upload manually with 'shp2pgsql'\n gadm.org > gadm36_JPN_1.shp > name_1='Okinawa'" )
l2.config(bg=misc_color)  
l2.grid(row=4,column=1)

l000=Label(win,text="_____________________________")
l000.grid(row=5,column=1)

l1=Label(win,text="1. Select Input Files",font=('Helvetica', 18, 'bold'))
l1.config(bg=head_color)  
l1.grid(row=7,column=1)	
b2 = Button(win, text="Select CSV File", command=select_csv_file)
b2.grid( row=8, column=1)
lbl_csv_file=Label(win,text="")
lbl_csv_file.grid(row=8,column=2)



l11=Label(win,text="_____________________________")
l11.grid(row=10,column=1)
l3=Label(win,text="2. Clean Probe data",font=('Helvetica', 18, 'bold'))
l3.config(bg=head_color) 
l3.grid(row=11,column=1)

l5=Label(win,text="Retain Cars Samples (%)")
l5.grid(row=12,column=1)


# dropdown for getting sampling %
sampling_val = [100,5,10,20,30,40,50,60,70,80,90]
svar_sample =  StringVar()
svar_sample.set(sampling_val[0])     #<-- Setting default item to servs's first item
#SAMPLING_PERCENT = sampling_val[0]          #<-- setting sv to default item
#drop_samples = OptionMenu(win, svar_sample,  command = get_sampling_percent, *sampling_val)
drop_samples = OptionMenu(win, svar_sample,  command = get_sampling_percent, *sampling_val)

drop_samples.grid(row=14, column=1)

btn_preprocess = Button(win, text="Preprocess CSV", command=preprocess_csv_file)
btn_preprocess.grid( row=16, column=1)
lbl_preprocess=Label(win,text="")
lbl_preprocess.grid(row=16,column=2)

l12=Label(win,text="_____________________________")
l12.grid(row=18,column=1)

l4=Label(win,text="3.Generate Routes",font=('Helvetica', 18, 'bold'))
l4.config(bg=head_color) 
l4.grid(row=19,column=1)


btn_generate_routes = Button(win, text="Generate Routes", command=generate_routes)
btn_generate_routes.grid( row=21, column=1)
lbl_generate_routes=Label(win,text="")
lbl_generate_routes.grid(row=22,column=1)
 
win.mainloop()



