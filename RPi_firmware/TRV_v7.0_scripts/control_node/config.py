# -*- coding: utf-8 -*-

# This script gets configuration settings for the node from the server
# and saves it to local JSON file. It also sends back MAC and IP addresses,
# along with current date time and running scripts back to the server,
# and sets automation scripts on the node.

# Developed by Akram Ali
# Last updated on: 02/17/2020

import os
import requests
import json
import time
import socket
import shlex
import subprocess
from pathlib import Path
from datetime import datetime

url = 'config.elemental-platform.com'
get_url = 'http://config.elemental-platform.com/wp-json/acf/v3/nodes?slug[]='
put_url = 'http://config.elemental-platform.com/wp-json/acf/v3/nodes/'
auth = ('node', 'vvET(G6^kmkhx)l!!Zqnd@)^')

control_strategies = ['manual', 'enforced_schedule', 'check_motion', 'pid_temp', 'pid_temp_motion']
scripts = ['config','read_GPIO', 'read_serial', 'write_serial','set_PWM','datalogger',
'monitor_core_temp','preheat','enforce_schedule','check_motion','pid_temp'] # set all scripts to check if they're running
reboot_flag = False
put_config_flag = False

control_node_id_dir = '/home/pi/control_node'
json_dir = '/home/pi/control_node/'
temp_data_dir = '/home/pi/datalogger/temp_data'

node_id = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]    # get node ID
wp_id = 0

mac = subprocess.check_output('cat /sys/class/net/wlan0/address', shell=True).strip()

time.sleep(0.1)	# give some time for wifi to connect and everything to load and settle down

# get IP address
def get_ip_address():
	try:
		ip = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True).strip()
		if ':' not in ip: # check if it's IPv4 and not local IPv6
			return ip
		else:
			return ''
	except:
		pass
		return ''
	

# check internet connection
def internet_connection():
	try:
		host = socket.gethostbyname(url)
		s = socket.create_connection((host, 80), 2)
		s.close()
		return True
	except:
		pass
	return False

# get current running scripts
def get_running_scripts():
	PIDs=[]
	script_status=[]
	ss = ''
	for s in scripts:
		cmd = "pgrep -f 'python %s.py'" % s
		try:
			output = subprocess.check_output(shlex.split(cmd), shell=False).decode("utf-8")
		except subprocess.CalledProcessError:
			output = ''
		PIDs.append(output)
		time.sleep(0.01)
	n=0

	for p in PIDs:
		n+=1
		if n == 6 or n == 8:
			script_status.append(' ')
		if p == '':
			script_status.append('0')
		else:
			script_status.append('1')
	ss = ''.join(script_status)
	return ss

# get node configuration from server
def get_config():
	global wp_id

	attempts = 0
	while attempts < 3:
		try:
			_response = requests.get(get_url+str(node_id), auth=auth)
			wp_id = _response.json()[0]['id']
			break
		except:
			attempts += 1
			time.sleep(1)
			_response = {}	# return empty json file
	return _response

# send back mac and ip address to server
def put_config(put_type):
	global wp_id
	global mac
	global ip

	# get node statuses
	running_scripts = get_running_scripts()
	last_updated = str(datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
	ct = os.popen("vcgencmd measure_temp").read()
	ct2 = ct.replace("temp=","")
	ct3 = ct2.replace("'C","")
	core_temp = ct3.replace("\n","")
	pwm = get_PWM()
	if config[0]['acf']['servo_type'] == 'normal':
		s_start = 635
		s_end = 150
	elif config[0]['acf']['servo_type'] == 'special_servo':
		s_start = 600
		s_end = 130
	pwm_percent = round((1 - ((int(pwm) - s_end)/(s_start - s_end))) * 100)
	current_valve_position = '%s (%s%%)' % (str(pwm), str(pwm_percent))

	network_info = {
		"fields": {
			"mac_address": mac,
			"ip_address": ip
		}
	}

	status = {
		"fields": {
			"last_updated": last_updated,
			"running_scripts": running_scripts,
			"core_temp": str(core_temp),
			"current_valve_position": current_valve_position
		}
	}

	reboot = {
		"fields": {
			"reboot": False
		}
	}

	setpoint = {
		"fields": {
			"override_setpoint": False
		}
	}

	if put_type == 'network':
		json_body = network_info
	elif put_type == 'status':
		json_body = status
	elif put_type == 'reboot':
		json_body = reboot
	elif put_type == 'override_setpoint':
		json_body = setpoint

	attempts = 0
	while attempts < 3:
		try:
			_response = requests.put(put_url+str(wp_id), json=json_body, auth=auth)
			time.sleep(1)
			if _response:
				return True
			else:
				return False
			break
		except:
			attempts += 1
			time.sleep(1)
			_response = {}
	return False
	

# save config json file
def save_config(response_json):
	attempts = 0
	while attempts < 3:
		try:
			with open(json_dir + 'config.json', 'w') as f:
				json.dump(response_json, f, ensure_ascii=False, indent=4)
			break
		except:
			attempts += 1
			time.sleep(0.1)

# rewrite old config json file
def save_old_config(response_json):
	attempts = 0
	while attempts < 3:
		try:
			with open(json_dir + '_config.json', 'w') as f:
				json.dump(response_json, f, ensure_ascii=False, indent=4)
			break
		except:
			attempts += 1
			time.sleep(0.1)

# read config json file
def load_config():
	attempts = 0
	while attempts < 3:
		try:
			with open(json_dir + 'config.json', 'r') as f:
				data = json.load(f)
			break
		except:
			attempts += 1
			time.sleep(0.1)
	return data

# read old config json file
def load_old_config():
	attempts = 0
	while attempts < 3:
		try:
			with open(json_dir + '_config.json', 'r') as f:
				data = json.load(f)
			break
		except:
			attempts += 1
			time.sleep(0.1)
	return data


# dump config json file
def dump_config(config, key, value):
	config[0]['acf'][key] = value

	attempts = 0
	while attempts < 3:
		try:
			with open(json_dir + 'config.json', 'w') as f:
				json.dump(config, f, indent=4)
			break
		except:
			attempts += 1
			time.sleep(0.1)

# get latest PWM value from file
def get_PWM():
	try:
		file = open('%s/%s.csv' % (temp_data_dir, node_id[0]),'r')
		data = file.readline()
		file.close()
	except:
		pass
	parsed_data = {}
	try:
		for p in data.strip().split(","): #strip() removes trailing \n
			k,v = p.split(":")
			parsed_data[k] = v if v else 0.00
		pwm = parsed_data.get('w')
		return pwm
	except:
		return 0

# delete old config files
def del_file(_file):
	fn = '%s/%s' % (control_node_id_dir, _file)
	my_file = Path(fn)
	if my_file.is_file():   # check if files exist
		os.remove(fn)   # delete file

# check and set control strategy
def set_control_strategy(_config):
	if 'control_strategy' in _config[0]['acf']:
		control_strategy = _config[0]['acf']['control_strategy']
		for cs in control_strategies:
			if control_strategy == cs:
				os.system("sudo sed -i '/%s/ s/#//g' /etc/rc.local" % cs)	# uncomment control strategy line only

			elif control_strategy != cs:
				os.system("sudo sed -i '/%s/ s/#//g' /etc/rc.local" % cs)	# uncomment control strategy line only
				os.system("sudo sed -i '/%s/s/^/#/' /etc/rc.local" % cs)	# comment line matching control strategy
		
		# for pid_temp and pid_temp_motion only
		if control_strategy == control_strategies[3]:
			os.system("sudo sed -i '/%s/s/^/#/' /etc/rc.local" % 'set_PWM')		# comment out set_PWM

		# for pid_temp_motion only
		elif control_strategy == control_strategies[4]:
			os.system("sudo sed -i '/%s/ s/#//g' /etc/rc.local" % control_strategies[2])	# uncomment control strategy line only
			os.system("sudo sed -i '/%s/ s/#//g' /etc/rc.local" % control_strategies[3])	# uncomment control strategy line only
			os.system("sudo sed -i '/%s/s/^/#/' /etc/rc.local" % 'set_PWM')		# comment out set_PWM

		# for all other strategies
		else:
			os.system("sudo sed -i '/%s/ s/#//g' /etc/rc.local" % 'set_PWM')	# uncomment set_PWM

def set_preheat(_config):
		preheat = _config[0]['acf']['preheat']

		if preheat:
			os.system("sudo sed -i '/preheat/ s/#//g' /etc/rc.local")	# uncomment preheat

		elif preheat is False:
			os.system("sudo sed -i '/preheat/ s/#//g' /etc/rc.local")	# uncomment preheat
			os.system("sudo sed -i '/preheat/s/^/#/' /etc/rc.local")	# comment preheat



# clear old config files on boot
# del_file('config.json')
# del_file('_config.json')

# get initial settings from server and return mac and ip address
if internet_connection() is True:
	response = get_config()
	if response:
		save_config(response.json())
		save_old_config(response.json())

current_time = time.time()
old_time = time.time()

# loop forever and keep checking for updated config
while True:
	# keep track of time
	current_time = time.time()
	
	if internet_connection() is True:
		response = get_config()
		if response:
			save_config(response.json())
		config = load_config()
		old_config = load_old_config()

		if not put_config_flag:
			ip = get_ip_address()
			if ip is not None or ip != '':
				put_response_network = put_config('network')
			else:
				put_response_network = False
			put_response_status = put_config('status')
			if put_response_network and put_response_status:
				put_config_flag = True


		if 'control_strategy' in config[0]['acf']:
			new_control_strategy = config[0]['acf']['control_strategy']
			old_control_strategy = old_config[0]['acf']['control_strategy']

			if old_control_strategy != new_control_strategy:
				set_control_strategy(config)
				reboot_flag = True
			else:
				pass
		
		if 'preheat' in config[0]['acf']:
			new_preheat = config[0]['acf']['preheat']
			old_preheat = old_config[0]['acf']['preheat']

			if new_preheat != old_preheat:
				set_preheat(config)
				reboot_flag = True
			else:
				pass
		
		if 'override_setpoint' in config[0]['acf']:
			if config[0]['acf']['override_setpoint'] is True:
				control_strategy = config[0]['acf']['control_strategy']
				if control_strategy == control_strategies[3] or control_strategy == control_strategies[4]:
					setpoint = config[0]['acf']['override_setpoint_temp_value']
				else:
					setpoint = config[0]['acf']['override_setpoint_value']
				os.system("sudo python %s/setpoint_override.py %s" % (control_node_id_dir, setpoint))	# set the override setpoint value in file

				# change local override flag to False so it does not get stuck in setpoint loop
				key = 'override_setpoint'
				value = False
				dump_config(config, key, value)
				
				# change override flag on server
				put_config('override_setpoint')

		
		if 'reboot' in config[0]['acf']:
			if config[0]['acf']['reboot'] is True:

				# change local reboot to False so it does not get stuck in bootloop
				key = 'reboot'
				value = False
				dump_config(config, key, value)

				# change reboot flag on server
				put_config('reboot')

				time.sleep(2)
				os.system("sudo reboot")
				time.sleep(5)


		# rewrite old config with new config
		if response:
			save_old_config(response.json())

		# reboot device to apply new control strategy & preheat settings
		if reboot_flag:
			os.system("sudo reboot")
		else:
			pass
		
		# update node status every hour
		if current_time - old_time >= 3600:
			old_time = time.time()
			ip = get_ip_address()
			if ip is not None or ip != '':
				put_response_network = put_config('network')
			put_response_status = put_config('status')
			time.sleep(1)

	time.sleep(30)      # sleep few secs to let other stuff run in bg