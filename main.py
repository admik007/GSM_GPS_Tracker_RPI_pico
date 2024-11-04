import utime, time, ubinascii, machine, os, network, ntptime, socket, random
from machine import Pin, UART, I2C, ADC, WDT
from micropyGPS import MicropyGPS
from sx1262 import SX1262

# LoRa_SX1262
sx = SX1262(spi_bus=1, clk=10, mosi=11, miso=12, cs=3, irq=20, rst=15, gpio=2)
sx.begin(freq=868, bw=500.0, sf=12, cr=8, syncWord=0x12,
 power=-5, currentLimit=60.0, preambleLength=8,
 implicit=False, implicitLen=0xFF,
 crcOn=True, txIq=False, rxIq=False,
 tcxoVoltage=1.7, useRegulatorLDO=False, blocking=True)
#####################################################################
DEBUG = 1				# 1 / 0
WD = False				# True / False
#####################################################################


#####################################################################
#####################  DEFINITION OF VARIABLES  #####################
APN = "internet"
latitude = ""
longitude = ""
satellites  =""
GPStime = "" 
altitude = ""
time_zone = 0
altitude_past = 0
AL=''

NOSIGNAL = 1
MCC = ""
MNC = ""
BSIC = ""
CELLID = ""
CELLIDhex = ""
LAC = ""

counter = 0
TIMEOUT = 1000
MODEM_SIGNAL = False


# SERVER
HOST="http://gps.server.dom"


#WatchDog
if (WD == True):
 wdt=WDT(timeout=8388)


# MY ID
my_id = ubinascii.hexlify(machine.unique_id()).decode()
DEVICE = my_id


# BATTERY STATUS
analogIn = ADC(26)


# CPU TEMPERATURE
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)


# DATE TIME
rtc=machine.RTC()


# LED STATUS
led = machine.Pin("LED", machine.Pin.OUT)
led.value(1)

# BUTTON CHECK
sim_d_key = machine.Pin(14, machine.Pin.OUT)						#GP14 (19)
sim_u_key = machine.Pin(17, machine.Pin.OUT)						#GP17 (22)
gps_sim   = machine.Pin(18, machine.Pin.OUT)						#GP18 (24)



# GSM SETTINGS
uart_gsm_port = 0
uart_gsm_baute = 115200
gsm_module = machine.UART(uart_gsm_port, uart_gsm_baute)
print(gsm_module)


# GPS SETTINGS
uart_gps_port = 1
uart_gps_baute = 9600
gps_module = machine.UART(uart_gps_port, uart_gps_baute)
print(gps_module)

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
 if (WD == True):
  wdt.feed()
 led.value(0)
 time.sleep(.2)
 

# POWER ON/OFF THE MODULE
def power_on_off():
    pwr_key_slep = machine.Pin(sim_d_key, machine.Pin.OUT)
    pwr_key_wkup = machine.Pin(sim_u_key, machine.Pin.OUT)
    print("Power off")
    pwr_key_slep.value(0)
    pwr_key_wkup.value(0)
    utime.sleep(1)
    print("Power on")
    pwr_key_slep.value(1)
    pwr_key_wkup.value(1)
    utime.sleep(6)


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


# WAIT RESPONSE INFO
def wait_resp_info(timeout=TIMEOUT):
 blink()
 prvmills = utime.ticks_ms()
 info = b""
 while (utime.ticks_ms()-prvmills) < timeout:
  if gsm_module.any():
   info = b"".join([info, gsm_module.read(1)])
 return info


# SEND AT COMMAND
def send_at(cmd, back, timeout=TIMEOUT):
 blink()
 rec_buff = b''
 gsm_module.write((cmd+'\r\n').encode())
 prvmills = utime.ticks_ms()
 while (utime.ticks_ms()-prvmills) < timeout:
  if gsm_module.any():
   rec_buff = b"".join([rec_buff, gsm_module.read(1)])
 if rec_buff != '':
  if back not in rec_buff.decode():
   print(cmd + ' back:\t' + rec_buff.decode())
   return 0
  else:
   print(rec_buff.decode())
   return 1
 else:
  print(cmd + ' no responce')


# SEND AT COMMAND AND RETURN RESPONSE INFORMATION
def send_at_wait_resp(cmd, back, timeout=TIMEOUT):
 blink()
 rec_buff = b''
 gsm_module.write((cmd + '\r\n').encode())
 prvmills = utime.ticks_ms()
 while (utime.ticks_ms() - prvmills) < timeout:
  if gsm_module.any():
   rec_buff = b"".join([rec_buff, gsm_module.read(1)])
 if rec_buff != '':
  if back not in rec_buff.decode():
   print(cmd + ' back:\t' + rec_buff.decode())
  else:
   print(rec_buff.decode())
 else:
  print(cmd + ' no responce')
  print("Response information is: ", rec_buff)
 return rec_buff


# SEND AT COMMAND TO HTTP
def http_get_sim(url):
 print('>>>>>>>> START-SIM <<<<<<<< ')
 blink()
 global MODEM_SIGNAL
 send_at('AT+HTTPINIT', 'OK')
 send_at('AT+HTTPPARA=\"CID\",1', 'OK')
 send_at('AT+HTTPPARA=\"URL\",\"'+URL+'\"', 'OK')
 if send_at('AT+HTTPACTION=0', '200', 5000):
  MODEM_SIGNAL = True
  gsm_module.write(bytearray(b'AT+HTTPREAD\r\n'))
  rec_buff = wait_resp_info(9000)
  print("resp is :", rec_buff.decode())
  if (DEBUG == 1): 
   print('>>>>>>>> URL send done <<<<<<<< ')
  else:
   MODEM_SIGNAL = False
   print("Get HTTP failed, please check and try again\n")
   if (DEBUG == 1): 
    print('>>>>>>>> Get HTTP failed, please check and try again <<<<<<<< ')
  send_at('AT+HTTPTERM', 'OK') 
  print('>>>>>>>> END-SIM <<<<<<<< ')
 

# GET BTS INFO
def get_bts_info():
 print('-----------------------------')
 global MCC, MNC, BSIC, CELLID, LAC
 send_at("AT+CENG=4,0", "OK")
 gsm_module.write(bytearray(b'AT+CENG?\r\n'))
 rec_buff = wait_resp_info()
 buff = str(rec_buff)
 parts = buff.split(',')
 if (DEBUG == 1): 
  print(parts)
 if (parts[0] != "b''"):
  if (parts[0] != "b'AT+CENG?\\r\\r\\n+CENG: 0"):
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


# MODULE STARTUP DETECTION
def check_start():
    global MODEM_SIGNAL
    while True:
        # simcom module gsm_module may be fool,so it is better to send much times when it starts.
        gsm_module.write(bytearray(b'ATE1\r\n'))
        utime.sleep(2)
        gsm_module.write(bytearray(b'AT\r\n'))
        rec_temp = wait_resp_info()
        if 'OK' in rec_temp.decode():
            print('SIM868 is ready\r\n' + rec_temp.decode())
            MODEM_SIGNAL = True
            break
        else:
            power_on_off()
            print('SIM868 is starting up, please wait...\r\n')
            MODEM_SIGNAL = False
            utime.sleep(2)


# CHECK THE NETWORK STATUS
def check_network():
    global MODEM_SIGNAL
    for i in range(1, 3):
        if send_at("AT+CGREG?", "0,1") == 1:
            print('SIM868 is online\r\n')
            MODEM_SIGNAL = True
            break
        else:
            print('SIM868 is offline, please wait...\r\n')
            MODEM_SIGNAL = False
            utime.sleep(5)
            continue
    send_at("AT+CPIN?", "OK")
    send_at("AT+CSQ", "OK")
    send_at("AT+COPS?", "OK")
    send_at("AT+CGATT?", "OK")
    send_at("AT+CGDCONT?", "OK")
    send_at("AT+CSTT?", "OK")
    send_at("AT+CSTT=\""+APN+"\"", "OK")
    send_at("AT+CIICR", "OK")
    send_at("AT+CIFSR", "OK")


# BEARER CONFIGURATION
def bearer_config():
    send_at('AT+SAPBR=3,1,\"Contype\",\"GPRS\"', 'OK')
    send_at('AT+SAPBR=3,1,\"APN\",\"'+APN+'\"', 'OK')
    send_at('AT+SAPBR=1,1', 'OK')
    send_at('AT+SAPBR=2,1', 'OK')
#   send_at('AT+SAPBR=0,1', 'OK')

#####################  DEFINITION OF FUNCTIONS  #####################
#####################################################################

check_start()
check_network()
bearer_config()

#####################################################################
########################  START WITH SCRIPT  ########################
#####################################################################
while True:
 try:
  blink()

  CHARNR = 0
  timestamp=rtc.datetime()
  localdate=("%04d-%02d-%02dT%02d:%02d:%02d"%(timestamp[0:3] + timestamp[4:7]))

  get_bts_info()
  for CHAR in CELLID:
   CHARNR+=1
  if (CHARNR == 4 ): CELLID = '0'+CELLID
  if (CHARNR == 3 ): CELLID = '00'+CELLID
  if (CHARNR == 2 ): CELLID = '000'+CELLID
  if (CHARNR == 1 ): CELLID = '0000'+CELLID
  
  length = gps_module.any()
  print(length)
  if length > 0:
   data = gps_module.read(length)
   print('DATA: '+str(data))
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

  date_full = str(gps.datestamp)
  datefullpart = date_full.split(', ')

  DAYpart=datefullpart[0].split('[')
  DAY = str(DAYpart[1])
  if (DAY == '0'): DAY = str("0"+DAY)
  if (DAY == '1'): DAY = str("0"+DAY)
  if (DAY == '2'): DAY = str("0"+DAY)
  if (DAY == '3'): DAY = str("0"+DAY)
  if (DAY == '4'): DAY = str("0"+DAY)
  if (DAY == '5'): DAY = str("0"+DAY)
  if (DAY == '6'): DAY = str("0"+DAY)
  if (DAY == '7'): DAY = str("0"+DAY)
  if (DAY == '8'): DAY = str("0"+DAY)
  if (DAY == '9'): DAY = str("0"+DAY)
      
  MONTHpart=datefullpart[1]
  MONTH = str(MONTHpart)    
  if (MONTHpart == '0'): MONTH = str("0"+MONTHpart)
  if (MONTHpart == '1'): MONTH = str("0"+MONTHpart)
  if (MONTHpart == '2'): MONTH = str("0"+MONTHpart)
  if (MONTHpart == '3'): MONTH = str("0"+MONTHpart)
  if (MONTHpart == '4'): MONTH = str("0"+MONTHpart)
  if (MONTHpart == '5'): MONTH = str("0"+MONTHpart)
  if (MONTHpart == '6'): MONTH = str("0"+MONTHpart)
  if (MONTHpart == '7'): MONTH = str("0"+MONTHpart)
  if (MONTHpart == '8'): MONTH = str("0"+MONTHpart)
  if (MONTHpart == '9'): MONTH = str("0"+MONTHpart)

  YEARpart=datefullpart[2].split(']')
  YEAR = '20'+str(YEARpart[0])
  if (YEAR == '200'): YEAR = '2000'
  if (YEAR == '2080'): YEAR = '2000'
  date_full = YEAR+'-'+MONTH+'-'+DAY

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
 
  GPStime=date_full+'T'+datetime+'Z'
  print('-----------------------------')
  print('Fix:    ' + str(fixstat))
  print('Lat:    ' + latitude)
  print('Lon:    ' + longitude)
  print('Alt:    ' + altitude)
  print('Sat:    ' + satellites)
  print('Dir:    ' + course)
  print('Spd:    ' + speed)
  print('Date:   ' + date_full)
  print('Time:   ' + datetime)
  print('Gtime:  ' + GPStime)
  print('Dev:    ' + DEVICE)
  print('MCC:    ' + MCC)
  print('MNC:    ' + MNC)
  print('BSIC:   ' + BSIC)
  print('CID:    ' + CELLID)
  print('LAC:    ' + LAC)
  print('SIGNAL: ' + str(MODEM_SIGNAL))

  print('-----------------------------')
  counter+=1
  led.value(0)
  
  #####################################################################
  ####################### READING FROM SENSORS ########################
  reading = sensor_temp.read_u16() * conversion_factor 
  cputemp = str(round(27 - (reading - 0.706)/0.001721,2))
  sensorValue = analogIn.read_u16()
  voltage = round(sensorValue * (3.3 / 65535),2)
  voltage_per = round(voltage / 1.365 * 100,0)
  ####################### READING FROM SENSORS ########################
  #####################################################################

  URL=str(HOST+"?lat="+latitude+"&lon="+longitude+"&sat="+satellites+"&alt="+altitude+"&time="+str(GPStime)+"&speed="+str(speed.split(' ')[0])+"&dir="+str(course)+"&bat="+str(voltage_per)+"&devicerpi="+DEVICE+"&temprpi="+cputemp+"&MCC="+MCC+"&MNC="+MNC+"&BSIC="+BSIC+"&CELLID="+CELLID+"&LAC="+LAC+"&FIX="+str(fixstat))
 
  #####################################################################
  ######################### DO REQUEST TO URL #########################
  print("\n\n")
  print("================================================================================================================================================================")
  print(str(counter)+" = "+URL)

  print('Sending via LORA') 
  sx.send(b''+URL)
  print('Done\n')
  
  if (MODEM_SIGNAL == False):
   if(str(fixstat) != '0'):
    if(YEAR != '2000'):
     print('Write to file')
     file=open('gps_'+date_full+'.gpx','a')
     file.write(URL+"\n")
     file.flush()
     print('Done\n')
#   check_start()
   check_network()
   bearer_config()


  if (MODEM_SIGNAL == True):
   print('Sending via MODEM') 
   http_get_sim(URL)
   print('Done\n')
   
  print("================================================================================================================================================================")
  print("\n")

  if (counter == 600):
   counter = 0
   while True:
    print(str(counter))
    led.value(1)
    time.sleep(.5)
    led.value(0)
    time.sleep(.5)
    counter+=1

######################### DO REQUEST TO URL #########################
#####################################################################

#####################################################################
###################### DO SOMETHING ON ERRORS ####################### 
 except OSError as e:
  print('connection closed - OS error')
  machine.reset()

 except MemoryError:
  print('connection closed - MEM error')
  machine.reset()
###################### DO SOMETHING ON ERRORS #######################
#####################################################################
