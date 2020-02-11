# Pi core temp data logger script by AKstudios
# Updated on 11/6/2018

import os
import time
from datetime import datetime

time.sleep(5)

while True:
        t = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        ct = os.popen("vcgencmd measure_temp").read()
        ct2 = ct.replace("temp=","")
        ct3 = ct2.replace("'C","")
        core = ct3.replace("\n","")
        # print (core)
        try:
            file = open('core_temp.csv','a')
            file.write(str(t))
            file.write(",")
            file.write(str(core))     # save core temperature in a csv file
            file.write("\n")
            file.close()
        except:
            pass
        time.sleep(60)
