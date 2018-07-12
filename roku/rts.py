from roku import Roku
from time import sleep
import roku.time_convert as tc
import threading

def default_target_template():
	print("This is a test!")

def real_target_template(fn, time):
	sleep(time)
	fn()

class Roku_Task_Scheduler:
	# ms for months
	# hs for hours
	# mins for minutes
	# ss for seconds
	def __init__(self, fn=default_target_template, ms=0, hs=0, mins=0, ss=0):
		time_to_sleep = tc.convert_months_to_seconds(ms) + tc.convert_hours_to_seconds(hs) + tc.convert_minutes_to_seconds(mins) + ss
		
		t = threading.Thread(target=real_target_template, args=(fn, time_to_sleep))
		t.start()

		
		
