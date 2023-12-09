import utime, time, ntptime, ubinascii, network, machine, socket, dht, os
from machine import Pin, UART, I2C, ADC, WDT
from sx1262 import SX1262
from micropyGPS import MicropyGPS


#####################################################################
#####################  DEFINITION OF VARIABLES  #####################
# LoRa_SX1262
sx = SX1262(spi_bus=1, clk=10, mosi=11, miso=12, cs=3, irq=20, rst=15, gpio=2)
sx.begin(freq=868, bw=500.0, sf=12, cr=8, syncWord=0x12,
 power=-5, currentLimit=60.0, preambleLength=8,
 implicit=False, implicitLen=0xFF,
 crcOn=True, txIq=False, rxIq=False,
 tcxoVoltage=1.7, useRegulatorLDO=False, blocking=True)


latitude = ""
longitude = ""
satellites  =""
GPStime = ""
altitude = ""
MCC = ""
MNC = ""
BSIC = ""
CELLID = ""
CELLIDhex = ""
LAC = ""
lines = 0
counter = 0
TIMEOUT = 800


# SERVER
HOST="http://gps.ztk-comp.sk/"


#WatchDog
#wdt=WDT(timeout=8388)


# MY ID
my_id = ubinascii.hexlify(machine.unique_id()).decode()


# BATTERY STATUS
analogIn = ADC(26)


# CPU TEMPERATURE
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)


# DATE TIME
rtc=machine.RTC()


# LED STATUS
led = machine.Pin("LED", machine.Pin.OUT)



# INITIALIZE GPS MODULE
gps_module = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))		#GP1  (6), GP1  (2)
#gps_module = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))		#GP4  (6), GP5  (7)
time_zone = 0
gps = MicropyGPS(time_zone)
altitude_past = 0
AL=''
#####################  DEFINITION OF VARIABLES  #####################
#####################################################################


#####################################################################
#####################  DEFINITION OF FUNCTIONS  #####################
# DIODE BLINK
def blink():
 led.value(1)
 time.sleep(.1)
# wdt.feed()
 led.value(0)
 time.sleep(.2)
 

# CONVERT COORDINATES
def convert_coordinates(sections):
 if sections[0] == 0:  # sections[0] contains the degrees
  return None
 
 # sections[1] contains the minutes
 data = sections[0] + (sections[1] / 60.0)
 
 # sections[2] contains 'E', 'W', 'N', 'S'
 if sections[2] == 'S':
  data = -data
 if sections[2] == 'W':
  data = -data
 
 data = '{0:.5f}'.format(data)  # 6 decimal places
 return str(data)




# GET BTS INFO
def get_bts_info():
 print('-----------------------------')
 global MCC, MNC, BSIC, CELLID, LAC
 send_at("AT+CENG=4,0", "OK")
 uart.write(bytearray(b'AT+CENG?\r\n'))
 rec_buff = wait_resp_info()
 buff = str(rec_buff)
 parts = buff.split(',')
 print(parts)
 if (parts[0] != "b''"):
  MCC=parts[5]
  MNC=parts[6]
  BSIC=parts[7]
  CELLIDhex=parts[8]
  CELLIDdec = int(CELLIDhex, 16)
  CELLID=str(CELLIDdec)
  LAChex=parts[9]
  LACdec = int(LAChex, 16)
  LAC=str(LACdec)
 else:
  MCC="0"
  MNC="0"
  BSIC="0"
  CELLIDhex="0"
  CELLIDdec="0"
  CELLID="0"
  LAChex="0"
  LACdec="0"
  LAC="0"


#####################  DEFINITION OF FUNCTIONS  #####################
#####################################################################


#####################################################################
########################  START WITH SCRIPT  ########################
#####################################################################
while True:
 try:
  blink()

  timestamp=rtc.datetime()
  localdate=("%04d-%02d-%02dT%02d:%02d:%02d"%(timestamp[0:3] + timestamp[4:7]))
 
  length = gps_module.any()
#  print(length)
  if length > 0:
   data = gps_module.read(length)
   for byte in data:
    message = gps.update(chr(byte))

  latitude = convert_coordinates(gps.latitude)
  longitude = convert_coordinates(gps.longitude)
  fixstat = gps.fix_stat
  altitude_full = str(gps.altitude)
  altitudepart = altitude_full.split('.')
  altitude = altitudepart[0]
    
  if (str(altitude) > str(altitude_past)):
   altitude_past = str(altitude)
   AL='+'
  if (str(altitude) < str(altitude_past)):
   altitude_past = str(altitude)
   AL='-'

  course_full = str(gps.course)
  coursepart = course_full.split('.')
  course = coursepart[0]
 
  satellites = str(gps.satellites_in_use)
  speed = str(gps.speed_string(unit='kph'))
  date = str(gps.date_string(formatting='s_ymd', century='20'))

  datetime_full = str(gps.timestamp)
  datetimepart = datetime_full.split(', ')
  HOURpart=datetimepart[0].split('[')
  HOUR = str(HOURpart[1])
  if (HOURpart[1] == '0'): HOUR = str("0"+HOURpart[1])
  if (HOURpart[1] == '1'): HOUR = str("0"+HOURpart[1])
  if (HOURpart[1] == '2'): HOUR = str("0"+HOURpart[1])
  if (HOURpart[1] == '3'): HOUR = str("0"+HOURpart[1])
  if (HOURpart[1] == '4'): HOUR = str("0"+HOURpart[1])
  if (HOURpart[1] == '5'): HOUR = str("0"+HOURpart[1])
  if (HOURpart[1] == '6'): HOUR = str("0"+HOURpart[1])
  if (HOURpart[1] == '7'): HOUR = str("0"+HOURpart[1])
  if (HOURpart[1] == '8'): HOUR = str("0"+HOURpart[1])
  if (HOURpart[1] == '9'): HOUR = str("0"+HOURpart[1])
    
  MINUTEpart=datetimepart[1]
  MINUTE = str(MINUTEpart)    
  if (MINUTEpart == '0'): MINUTE = str("0"+MINUTEpart)
  if (MINUTEpart == '1'): MINUTE = str("0"+MINUTEpart)
  if (MINUTEpart == '2'): MINUTE = str("0"+MINUTEpart)
  if (MINUTEpart == '3'): MINUTE = str("0"+MINUTEpart)
  if (MINUTEpart == '4'): MINUTE = str("0"+MINUTEpart)
  if (MINUTEpart == '5'): MINUTE = str("0"+MINUTEpart)
  if (MINUTEpart == '6'): MINUTE = str("0"+MINUTEpart)
  if (MINUTEpart == '7'): MINUTE = str("0"+MINUTEpart)
  if (MINUTEpart == '8'): MINUTE = str("0"+MINUTEpart)
  if (MINUTEpart == '9'): MINUTE = str("0"+MINUTEpart)
   
  SECONDpart=datetimepart[2].split(']')
  SECONDpart2=SECONDpart[0].split('.')
  SECONDpart=SECONDpart2[0]
  SECOND = str(SECONDpart)
  if (SECONDpart == '0'): SECOND = str("0"+SECONDpart)
  if (SECONDpart == '1'): SECOND = str("0"+SECONDpart)
  if (SECONDpart == '2'): SECOND = str("0"+SECONDpart)
  if (SECONDpart == '3'): SECOND = str("0"+SECONDpart)
  if (SECONDpart == '4'): SECOND = str("0"+SECONDpart)
  if (SECONDpart == '5'): SECOND = str("0"+SECONDpart)
  if (SECONDpart == '6'): SECOND = str("0"+SECONDpart)
  if (SECONDpart == '7'): SECOND = str("0"+SECONDpart)
  if (SECONDpart == '8'): SECOND = str("0"+SECONDpart)
  if (SECONDpart == '9'): SECOND = str("0"+SECONDpart) 
  datetime = HOUR+':'+MINUTE+':'+SECOND 

  if(str(fixstat) == '0'):
   latitude = '0.000000'
   longitude = '0.000000'
   altitude = '0'



  msg, err = sx.recv()
  if len(msg) > 0:
#   print(msg)
   buff = str(msg)
   parts = buff.split(';')
#b'e661385283997828;231;02;62;48503;3;22.83;92.0;48.71905;21.20804;329;10;2021-01-01T00:31:16Z'

   if (parts[0] != "b''"):
    DEV = parts[0]
    DEVparts = DEV.split("'")
    DEVICE = DEVparts[1]
    MCC = parts[1]
    MNC = parts[2]
    BSIC = parts[3]
    CELLID = parts[4]
    LAC = parts[5]
    CPUTEMP = parts[6]
    VBAT = parts[7]
    if (DEVICE == 'e661385283997828'):
     print('Telekom')
   else:
    MCC="0"
    MNC="0"
    BSIC="0"
    CELLID="0"
    LAC="0"
   
  
  

  print('-----------------------------')
  print('Fix:  ' + str(fixstat))
  print('Lat:  ' + latitude)
  print('Lon:  ' + longitude)
  print('Alt:  ' + altitude)
  print('Sat:  ' + satellites)
  print('Dir:  ' + course)
  print('Spd:  ' + speed)
  print('Date: ' + date)
  print('Time: ' + datetime)
  print('Local:' + localdate)
  print('Dev:  ' + DEVICE)
  print('MCC:  ' + MCC)
  print('MNC:  ' + MNC)
  print('BSIC: ' + BSIC)
  print('CID:  ' + CELLID)
  print('LAC:  ' + LAC)
  print('-----------------------------')
  counter+=1
  led.value(0)
  if(date == '2000-00-00'):
   GPStime=localdate+'Z'
  else:
   GPStime=date+'T'+datetime+'Z'

  #####################################################################
  ####################### READING FROM SENSORS ########################
  reading = sensor_temp.read_u16() * conversion_factor 
  cputemp = str(round(27 - (reading - 0.706)/0.001721,2))

  sensorValue = analogIn.read_u16()
  voltage = round(sensorValue * (3.3 / 65535),2)
  voltage_per = round(voltage / 1.365 * 100,0)
  ####################### READING FROM SENSORS ########################
  #####################################################################
  
  URL=str(HOST+"?lat="+latitude+"&lon="+longitude+"&sat="+satellites+"&alt="+altitude+"&time="+str(GPStime)+"&bat="+str(voltage_per)+"&devicerpi="+DEVICE+"&temprpi="+cputemp+"&MCC="+MCC+"&MNC="+MNC+"&BSIC="+BSIC+"&CELLID="+CELLID+"&LAC="+LAC+"&C="+str(counter)+"&L="+str(lines))
 
  #####################################################################
  ######################### DO REQUEST TO URL #########################
  print("\n\n")
  print("================================================================================================================================================================")
  print(URL)
  print("================================================================================================================================================================")
  print("\n")  
######################### DO REQUEST TO URL #########################
#####################################################################
 except OSError as e:
  print('connection closed - OS error')
  machine.reset()

