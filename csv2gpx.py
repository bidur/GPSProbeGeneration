import sys,os
from datetime import datetime
import pandas as pd
import glob, shutil
from p3_generatePathPoints import remove_dir,check_dir

# "ap_id","timestamp","latitude","longitude" s.strip('""')


def process_line(line):
    def strip(s):
        return s.strip()
    name, timestamp, latitude, longitude = \
        map(strip, line.split(','))
    timestamp = datetime.strptime(timestamp.strip('"'),  '%Y-%m-%d %H:%M:%S')

    return dict(
		name=name,
        time=timestamp,
        latitude=latitude,
        longitude=longitude
        
    )


def gpx_header():
    return """\
<?xml version="1.0"?>
<gpx
 version="1.0"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xmlns="http://www.topografix.com/GPX/1/0"
 xsi:schemaLocation="http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd">
  <trk>
    <trkseg>
"""


def gpx_footer():
    return """\
    </trkseg>
  </trk>
</gpx>
"""


def gpx_datapoint(data):
    foo = data.copy()
    foo['time'] = data['time'].isoformat()
    return """\
<trkpt lat="{latitude}" lon="{longitude}">
  <name>{name}</name>
  <time>{time}</time>
</trkpt>""".format(**foo)


def output_xml(datapoints, output_file):
    print_line = gpx_header() 
    for datum in datapoints:
        print_line +=  gpx_datapoint(datum) 
    print_line +=  gpx_footer()  
    
    #print ("complete")
    f = open(output_file, "w")
    f.write(print_line)
    f.close()


def convert_csv2gpx(csv_dir, gpx_dir):
	
	for fname in glob.glob(csv_dir+'*.csv'):
		head, tail = os.path.split(fname)
		output_file = gpx_dir + tail +'.gpx'
		with open(fname, 'r') as f:
			lines = f.readlines()
			
		datapoints = map(process_line, lines[1:])
		output_xml(datapoints, output_file)
	
	return None
	
'''
def check_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        
def remove_dir(path):
	if  os.path.exists(path):
		 #os.system("rm -rf "+path)
		 shutil.rmtree(path)
'''	
def prepare_csv_files(df,csv_dir):
	
	# clean old files
	#remove_dir(csv_dir)
	#check_dir(csv_dir)
	#
	
	arr_ap_ids = df.ap_id.unique()
	
	cnt = 0
	for ap_id in arr_ap_ids:
		df_single_ap = df.query('ap_id=="'+ap_id+'"')
		
		if len(df_single_ap) < 10:# skip ap_id with less than 10 data points
			continue
		
		cnt += 1
		
		df_single_ap.to_csv(csv_dir+ap_id+'.csv',index=False)
	
	print (cnt ,' csv prepared: ', csv_dir)
	
	return None
'''		
	
import glob
path = "/media/bidur/349875C714C5228F/Miyazaki_research/mobilityProject/staypointAnalysis/ap520057/input/csv/*.csv"
for fname in glob.glob(path):
    print(fname)	
'''
'''
if __name__ == "__main__":
    
    #input_file= 'AP520057.csv'
    input_file = '/media/bidur/349875C714C5228F/Miyazaki_research/mobilityProject/data/Okinawa_fullDay_clipped.csv'
    
    csv_dir = 'input/csv/'
    gpx_dir = 'input/data4gh/'
    remove_dir(csv_dir)
    remove_dir(gpx_dir)
    check_dir(csv_dir)
    check_dir(gpx_dir)
    
    prepare_csv_files(input_file, csv_dir)
    
    convert_csv2gpx(csv_dir,gpx_dir)
'''

#https://github.com/des4maisons/csv-to-gpx/blob/master/csv-to-gpx.py
