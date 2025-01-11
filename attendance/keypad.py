from pad4pi import rpi_gpio
import sqlite3
import sys
import pyfingerprint
import I2C_LCD_driver
from time import *
import datetime
import hashlib
from pyfingerprint import PyFingerprint
import calendar
import time

###connceting to the lcd driver
mylcd = I2C_LCD_driver.lcd()
def finger():
	## Search for a finger
	##

	## Tries to initialize the sensor
	try:
		f = PyFingerprint('/dev/serial0', 9600, 0xFFFFFFFF, 0x00000000)

		if ( f.verifyPassword() == False ):
			raise ValueError('The given fingerprint sensor password is wrong!')
			startChoice()
	except Exception as e:
		print('The fingerprint sensor could not be initialized!')
		print('Exception message: ' + str(e))
		startChoice()

	## Gets some sensor information
	print('Currently used templates: ' + str(f.getTemplateCount()))

	## Tries to search the finger and calculate hash
	try:
		mylcd.lcd_clear()
		mylcd.lcd_display_string('Waiting for finger..',2)

		## Wait that finger is read
		while ( f.readImage() == False ):
			pass

		## Converts read image to characteristics and stores it in charbuffer 1
		f.convertImage(0x01)

		## Searchs template
		result = f.searchTemplate()

		positionNumber = result[0]
		accuracyScore = result[1]

		if ( positionNumber == -1 ):
			mylcd.lcd_clear()
			mylcd.lcd_display_string('No match found!')
			sleep(2)
			mylcd.lcd_clear()
			startChoice()
		else:
			mylcd.lcd_clear()
			today_name = datetime.date.today()
			if calendar.day_name[today_name.weekday()] != ('Sunday' or 'Saturday'):
				## Generating TIME VALUES
				now = datetime.datetime.now()
				my_time_string_10 = "10:30:00"
				my_time_string_12 = "12:30:00"
				my_time_string_13 = "13:29:59"
				my_time_string_14 = "14:30:00"
				my_time_string_16 = "16:00:01"
				time_10 = datetime.datetime.strptime(my_time_string_10, "%H:%M:%S")
				time_12 = datetime.datetime.strptime(my_time_string_12, "%H:%M:%S")
				time_13 = datetime.datetime.strptime(my_time_string_13, "%H:%M:%S")
				time_14 = datetime.datetime.strptime(my_time_string_14, "%H:%M:%S")
				time_16 = datetime.datetime.strptime(my_time_string_16, "%H:%M:%S")

				# I am supposing that the date must be the same as now
				time_10 = now.replace(hour=time_10.time().hour, minute=time_10.time().minute, second=time_10.time().second, microsecond=0)
				time_12 = now.replace(hour=time_12.time().hour, minute=time_12.time().minute, second=time_12.time().second, microsecond=0)
				time_13 = now.replace(hour=time_13.time().hour, minute=time_13.time().minute, second=time_13.time().second, microsecond=0)
				time_14 = now.replace(hour=time_14.time().hour, minute=time_14.time().minute, second=time_14.time().second, microsecond=0)
				time_16 = now.replace(hour=time_16.time().hour, minute=time_16.time().minute, second=time_16.time().second, microsecond=0)

				print('Found template at position #' + str(positionNumber))
				mylcd.lcd_display_string('PLEASE WAIT',2,3)

				## Create Hash Value for finger
				##

				## Loads the found template to charbuffer 1
				f.loadTemplate(positionNumber, 0x01)

				## Downloads the characteristics of template loaded in charbuffer 1
				characterics = str(f.downloadCharacteristics(0x01)).encode('utf-8')
				val_hash = hashlib.sha256(characterics).hexdigest()
				## Hashes characteristics of template
				print('SHA-2 hash of template: ' + val_hash)

				## GETTING INFORMATION FROM DATABASE
				conn = sqlite3.connect('/home/pi/Desktop/pro/attendance-20180412T122709Z-001/attendance/app.db')
				curs = conn.cursor()
				db_val = curs.execute('SELECT rollnum, hashval from finger_store where hashval in (values(?))', [val_hash])
				for row in db_val:
					ext_id = row[0]
					mylcd.lcd_clear()
					mylcd.lcd_display_string("YOUR ID NUMBER:",2,2)
					mylcd.lcd_display_string(ext_id,3,3)
					sleep(2)
					mylcd.lcd_clear()
				conn.commit()
				conn.close()

				con = sqlite3.connect('/home/pi/Desktop/pro/attendance-20180412T122709Z-001/attendance/app.db')
				curs2 = con.cursor()
				curs2.execute('SELECT date from attendance where (date, rollnum) in (values(?, ?))', (datetime.date.today(), ext_id))
				d = curs2.fetchone()
				con.close()

				if d == None:
					con = sqlite3.connect('/home/pi/Desktop/pro/attendance-20180412T122709Z-001/attendance/app.db')
					c = con.cursor()
					c.execute('INSERT INTO attendance (rollnum,date) values(?, ?)',(ext_id, datetime.date.today()))
					con.commit()
					con.close()
				## GETTING INFORMATION FROM DATABASE
				con = sqlite3.connect('/home/pi/Desktop/pro/attendance-20180412T122709Z-001/attendance/app.db')
				curs2 = con.cursor()
				curs2.execute('SELECT status,statusexit,statusnoon,statusnoonexit from attendance where (date, rollnum) in (values(?, ?))', (datetime.date.today(), ext_id))
				row = curs2.fetchall()
				for all in row:
					status1 = all[0]
					status2 = all[1]
					status3 = all[2]
					status4 = all[3]
				con.close()

				if status1 == 'absent':
					if now < time_10:
						con = sqlite3.connect('/home/pi/Desktop/pro/attendance-20180412T122709Z-001/attendance/app.db')
						c = con.cursor()
						c.execute('UPDATE attendance Set status = ? where (rollnum, date) in (values(?, ?))',('present', ext_id, datetime.date.today()))
						con.commit()
						con.close()
						mylcd.lcd_display_string("Attendance Success for",1)
						mylcd.lcd_display_string(" this Morining",2)
						sleep(2)
						mylcd.lcd_clear()
						mylcd.lcd_display_string("Dont forgot to ",1)
						mylcd.lcd_display_string("comeback after 12:30 PM",2)
						sleep(2)
						mylcd.lcd_clear()
					elif (now >= time_10) and (now <= time_13):
						mylcd.lcd_display_string("Sorry, You are Late today",1)
						sleep(2)
						mylcd.lcd_clear()
						mylcd.lcd_display_string("Come Afternoon ",2)
						mylcd.lcd_display_string("or Tomorrow",3)
						sleep(2)
						mylcd.lcd_clear()
					elif now > time_13:
						if status3 == 'absent':
							if now <= time_14:
								con = sqlite3.connect('/home/pi/Desktop/pro/attendance-20180412T122709Z-001/attendance/app.db')
								c = con.cursor()
								c.execute('UPDATE attendance Set statusnoon = ? where (rollnum, date) in (values(?, ?))',('present',ext_id,datetime.date.today()))
								con.commit()
								con.close()
								mylcd.lcd_display_string("Attendance Success ",1)
								mylcd.lcd_display_string("for this Afternoon",2)
								sleep(2)
								mylcd.lcd_clear()
								mylcd.lcd_display_string("Dont forgot to  ",1)
								mylcd.lcd_display_string("comeback after",2)
								mylcd.lcd_display_string("04:00 PM ",3)
								sleep(3)
								mylcd.lcd_clear()
							elif now > time_14:
								mylcd.lcd_display_string("Sorry, You are Late",2)
								sleep(2)
								mylcd.lcd_clear()
								mylcd.lcd_display_string("Please Come Early ",1)
								mylcd.lcd_display_string("Tomorrow",2,2)
								sleep(2)
								mylcd.lcd_clear()
						elif status3 == 'present':
							if now < time_16:
								mylcd.lcd_display_string("You're leaving Early",1)
								mylcd.lcd_display_string("Please come back",2)
								mylcd.lcd_display_string("after 4 PM",3)
								sleep(3)
								mylcd.lcd_clear()
							elif now >= time_16:
								if status4 == 'present':
									mylcd.lcd_display_string("Thought you were",1)
									mylcd.lcd_display_string("already in your home!",2)
									sleep(2)
									mylcd.lcd_clear()
								else:
									con = sqlite3.connect('/home/pi/Desktop/pro/attendance-20180412T122709Z-001/attendance/app.db')
									c = con.cursor()
									c.execute('UPDATE attendance Set statusnoonexit = ? where (rollnum, date) in (values(?, ?))',('present',ext_id,datetime.date.today()))
									con.commit()
									con.close()
									mylcd.lcd_display_string("Attendance Success,",2)
									mylcd.lcd_display_string(" Happy Day!",3,2)
									sleep(2)
									mylcd.lcd_clear()
				elif status1 == 'present':
					if now < time_12:
						mylcd.lcd_display_string("Not the time to",2)
						mylcd.lcd_display_string("leave",3,2)
						sleep(2)
						mylcd.lcd_clear()
					elif (now >= time_12) and (now <= time_13):
						con = sqlite3.connect('/home/pi/Desktop/pro/attendance-20180412T122709Z-001/attendance/app.db')
						c = con.cursor()
						c.execute('UPDATE attendance Set statusexit = ? where (rollnum, date) in (values(?, ?))',('present',ext_id,datetime.date.today()))
						con.commit()
						con.close()
						mylcd.lcd_display_string("Attendance Success",1)
						mylcd.lcd_display_string("Now Go and",2,2)
						mylcd.lcd_display_string("have your LUNCH :)",3)
						sleep(3)
						mylcd.lcd_clear()
					elif now > time_13:
						if status3 == 'absent':
							if now <= time_14:
								con = sqlite3.connect('/home/pi/Desktop/pro/attendance-20180412T122709Z-001/attendance/app.db')
								c = con.cursor()
								c.execute('UPDATE attendance Set statusnoon = ? where (rollnum, date) in (values(?, ?))',('present',ext_id,datetime.date.today()))
								con.commit()
								con.close()
								mylcd.lcd_display_string("Attendance Success ",1)
								mylcd.lcd_display_string("for this Afternoon",2)
								sleep(2)
								mylcd.lcd_clear()
								mylcd.lcd_display_string("Dont forgot to  ",1)
								mylcd.lcd_display_string("comeback after",2)
								mylcd.lcd_display_string("04:00 PM ",3)
								sleep(3)
								mylcd.lcd_clear()
							elif now > time_14:
								mylcd.lcd_display_string("Sorry, You are Late",2)
								sleep(2)
								mylcd.lcd_clear()
								mylcd.lcd_display_string("Please Come Early ",1)
								mylcd.lcd_display_string("Tomorrow",2,2)
								sleep(2)
								mylcd.lcd_clear()
						elif status3 == 'present':
							if now < time_16:
								mylcd.lcd_display_string("You're leaving Early",1)
								mylcd.lcd_display_string("Please come back",2)
								mylcd.lcd_display_string("after 4 PM",3)
								sleep(3)
								mylcd.lcd_clear()
							elif now >= time_16:
								if status4 == 'present':
									mylcd.lcd_display_string("Thought you were",1)
									mylcd.lcd_display_string("already in your home!",2)
									sleep(2)
									mylcd.lcd_clear()
								else:
									con = sqlite3.connect('/home/pi/Desktop/pro/attendance-20180412T122709Z-001/attendance/app.db')
									c = con.cursor()
									c.execute('UPDATE attendance Set statusnoonexit = ? where (rollnum, date) in (values(?, ?))',('present',ext_id,datetime.date.today()))
									con.commit()
									con.close()
									mylcd.lcd_display_string("Attendance Success,",2)
									mylcd.lcd_display_string(" Happy Day!",3,2)
									sleep(2)
									mylcd.lcd_clear()
			else:
				while True:
					mylcd.lcd_clear()
					mylcd.lcd_display_string('Today is a holiday',2,2)
					mylcd.lcd_clear()
					mylcd.lcd_display_string('So no ATTENDANCE, Enjoy!',3,2)
			startChoice()
	except Exception as e:
		print('Operation failed!')
		print('Exception message: ' + str(e))
		startChoice()

# Setup Keypad
KEYPAD = [
        ["1","2","3","A"],
        ["4","5","6","B"],
        ["7","8","9","C"],
        ["*","0","#","D"]
]

# same as calling: factory.create_4_by_4_keypad, still we put here fyi:
ROW_PINS = [16, 20, 21, 5] # BCM numbering; Board numbering is: 7,8,10,11 (see pinout.xyz/)
COL_PINS = [6, 13, 19, 26] # BCM numbering; Board numbering is: 12,13,15,16 (see pinout.xyz/)

factory = rpi_gpio.KeypadFactory()

# Try keypad = factory.create_4_by_3_keypad() or 
# Try keypad = factory.create_4_by_4_keypad() #for reasonable defaults
# or define your own:
keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS)

##Enroll
def enroll():
	mylcd.lcd_clear()
	mylcd.lcd_display_string('Enter Password:',1)
	paass = raw_input("Enter Password:")
	if paass == '4209':
		mylcd.lcd_clear()
		mylcd.lcd_display_string('Enter ID Number',1)
		r = raw_input("Enter ID Number: ")
		mylcd.lcd_display_string(r,2,2)
		sleep(2)
		## GETTING INFORMATION FROM DATABASE
		conn = sqlite3.connect('/home/pi/attendance/app.db')
		curs = conn.cursor()
		db_val = curs.execute('SELECT rollnum from finger_store where rollnum in (values(?))', [r])
		coun = (len(list(db_val)))
		if coun >= 1:
			mylcd.lcd_clear()
			mylcd.lcd_display_string('ID Number Already',1)
			mylcd.lcd_display_string('Taken',2,2)
			sleep(2)
			conn.commit()
			conn.close()
		else:
			conn.commit()
			conn.close()
			## Enrolls new finger
			##

			## Tries to initialize the sensor
			try:
				f = PyFingerprint('/dev/serial0', 9600, 0xFFFFFFFF, 0x00000000)

				if ( f.verifyPassword() == False ):
					mylcd.lcd_clear()
					mylcd.lcd_display_string('Contact Admin',1)
					sleep(2)
					raise ValueError('The given fingerprint sensor password is wrong!')
					
			except Exception as e:
				mylcd.lcd_clear()
				mylcd.lcd_display_string('Contact Admin',1)
				sleep(2)
				print('The fingerprint sensor could not be initialized!')
				print('Exception message: ' + str(e))
				startChoice()

			## Gets some sensor information
			mylcd.lcd_clear()
			mylcd.lcd_display_string('Currently used',1)
			mylcd.lcd_display_string('templates: ',2)
			mylcd.lcd_display_string(str(f.getTemplateCount()),2,13)
			sleep(2)
			print('Currently used templates: ' + str(f.getTemplateCount()))

			## Tries to enroll new finger
			try:
				mylcd.lcd_clear()
				mylcd.lcd_display_string('Waiting for Finger',2,2)

				## Wait that finger is read
				while ( f.readImage() == False ):
					pass

				## Converts read image to characteristics and stores it in charbuffer 1
				f.convertImage(0x01)

				## Checks if finger is already enrolled
				result = f.searchTemplate()
				positionNumber = result[0]

				if ( positionNumber >= 0 ):
					mylcd.lcd_clear()
					mylcd.lcd_display_string('Template already',1)
					mylcd.lcd_display_string('exists at  ',2)
					mylcd.lcd_display_string('position # ',3)
					mylcd.lcd_display_string(str(positionNumber),3,13)
					sleep(3)
					print('Template already exists at position #' + str(positionNumber))
					startChoice()
				else:
					mylcd.lcd_clear()
					mylcd.lcd_display_string('Remove finger...',2,2)
					print('Remove finger...')
					time.sleep(2)
					
					mylcd.lcd_clear()
					mylcd.lcd_display_string('Waiting for same',2)
					mylcd.lcd_display_string(' finger again',3)
					print('Waiting for same finger again...')

					## Wait that finger is read again
					while ( f.readImage() == False ):
						pass

					## Converts read image to characteristics and stores it in charbuffer 2
					f.convertImage(0x02)

					## Compares the charbuffers
					if ( f.compareCharacteristics() == 0 ):
						mylcd.lcd_clear()
						mylcd.lcd_display_string('Fingers not matched',2)
						sleep(2)
						raise Exception('Fingers do not match')
					## Creates a template
					f.createTemplate()

					## Saves template at new position number
					positionNumber = f.storeTemplate()
					## Loads the found template to charbuffer 1
					f.loadTemplate(positionNumber, 0x01)

					## Downloads the characteristics of template loaded in charbuffer 1
					characterics = str(f.downloadCharacteristics(0x01)).encode('utf-8')

					## Hashes characteristics of template
					cre_hash = hashlib.sha256(characterics).hexdigest()
					conn = sqlite3.connect('/home/pi/attendance/app.db')
					curs = conn.cursor()
					curs.execute('INSERT INTO finger_store(rollnum, hashval, id) values(?, ?, ?)',(r, cre_hash, positionNumber))
					conn.commit()
					conn.close()
					mylcd.lcd_clear()
					mylcd.lcd_display_string('Finger enrolled',2)
					mylcd.lcd_display_string('Successfully!',3,2)
					sleep(2)
					print('New template position #' + str(positionNumber))
					startChoice()
				
			except Exception as e:
				print('Operation failed!')
				print('Exception message: ' + str(e))
				startChoice()
		
	else:
		mylcd.lcd_clear()
		mylcd.lcd_display_string('Your Not Authorized!',2)
		sleep(2)


## Prints Key

def printKey(key):
	print(key)
	if (key=="1"):
		finger()
		startChoice()
	elif (key=="2"):
		enroll()
		startChoice()
	else:
		mylcd.lcd_clear()
		mylcd.lcd_display_string('Sorry, Choose Again',2)
		sleep(2)
		startChoice()
		
def startChoice():
	## printKey will be called each time a keypad button is pressed
	mylcd.lcd_clear()
	mylcd.lcd_display_string('Press Button',1)
	mylcd.lcd_display_string('1. Attendance',2)
	mylcd.lcd_display_string('2. Registration',3)
	
## initializing Programming by calling the Start function
startChoice()

keypad.registerKeyPressHandler(printKey)


try:
	while(True):
		time.sleep(0.2)
except:
	keypad.cleanup()



#keypad.cleanup()
