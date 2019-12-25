# realtime data logger script by AKstudios
# Updated on 12/24/2019

from datetime import datetime
from pathlib import Path
import time
import os
import dictionary
import string

sensorTypes = list(string.ascii_lowercase)  # create list of alphabets that represent sensor types as described in dictionary
now = datetime.now()   # get current date/time
logging_start_time = now.strftime('%Y%m%d-%H%M%S')    # format datetime to use in filename
temp_data_dir = '/home/pi/datalogger/temp_data'
data_dir = '/home/pi/datalogger/data'
control_node_id_dir = '/home/pi/control_node'

node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]    # get node ID

# delete old temp csv files initially to allow only new data to be saved
for f in os.listdir(temp_data_dir):
    fn = '%s/%s' % (temp_data_dir,f)
    my_file = Path(fn)
    if my_file.is_file():   # check if files exist
        os.remove(fn)   # delete file

# create control node temp data file with setpoint = 0
try:
    file = open('/home/pi/datalogger/temp_data/%s.csv' % node_ID[0],'w')        # node ID
    file.write("i:%s,y:0,u:0" % node_ID[0])
    file.close()
except:
    pass

time.sleep(60) # sleep 60 seconds to let data come in first

# function to find, parse, log data files
def logdata(_dt,_temp_data):
    for f in _temp_data:      # loop over list of available temporary data files
        flag = None
        while flag is None:     # keep trying to read file till success
            try:
                file = open('%s/%s.csv' % (temp_data_dir, f),'r')        # get data from file
                dataline = file.readline()
                file.close()
                flag = 1
            except:
                pass

        # parse data
        parsed_data = {}
        try:
            for p in dataline.strip().split(","): #strip() removes trailing \n
                k,v = p.split(":")
                if v is not None:
                    parsed_data[k] = v
                else:
                    parsed_data[k] = 0.00

        except:
            pass

        id = parsed_data.pop('i', None) # get sensor id

        # save data to file
        filename = '%s/%s_%s.csv' % (data_dir, f, logging_start_time)
        my_file = Path(filename)
        if my_file.is_file():   # if file already exists, i.e., logging started
            try:
                file = open(filename,'a')   # open file in append mode
                file.write('%s' % (_dt))   # write formatted datetime
                for k in sensorTypes:
                    if k in parsed_data:
                        file.write(',')
                        file.write(parsed_data[k])
                    else:
                        pass
                file.write('\n')
                file.close()
                time.sleep(0.005)
            except:
                print ('Error: Failed to open file %s' % filename)
                pass

        else:   # file does not exist, write headers to it, followed by data. This should happen first time when creating file only
            try:
                file = open(filename,'w')   # open file in write mode
                file.write('Date/Time')
                for k in sensorTypes:
                    if k in parsed_data:
                        file.write(',')
                        file.write(dictionary.sensorName[k])
                    else:
                        pass
                file.write('\n')
                file.close()
                time.sleep(0.005)
            except:
                pass


# loop forever
while True:
     # this will log data every second
    for i in range(0,60):

        flag = None
        while flag is None:     # keep trying to match seconds with real time
            dt = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            second = datetime.now().strftime("%S")

            if int(second) == i:
                flag = 1
                break
            else:
                time.sleep(0.5)
                pass

        if int(second) == 0 and flag == 1:
            # read all temp file names every loop to check for new ones
            temp_data = [".".join(f.split(".")[:-1]) for f in os.listdir(temp_data_dir)]
            if len(temp_data) != 0:
                logdata(dt,temp_data)
        else:
            pass

        time.sleep(0.1) # sleep script so the CPU is not bogged down
