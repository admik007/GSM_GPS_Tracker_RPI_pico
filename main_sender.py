import machine, utime, ubinascii, random
#import time, os, network, socket
from sx1262 import SX1262

# LoRa_SX1262
sx = SX1262(spi_bus=1, clk=10, mosi=11, miso=12, cs=3, irq=20, rst=15, gpio=2)
sx.begin(freq=868, bw=500.0, sf=12, cr=8, syncWord=0x12,
 power=-5, currentLimit=60.0, preambleLength=8,
 implicit=False, implicitLen=0xFF,
 crcOn=True, txIq=False, rxIq=False,
 tcxoVoltage=1.7, useRegulatorLDO=False, blocking=True)
#####################################################################
#####################  DEFINITION OF FUNCTIONS  #####################
my_id = ubinascii.hexlify(machine.unique_id()).decode()
DEVICE = my_id

MCC = ""
MNC = ""
BSIC = ""
CELLID = ""
CELLIDhex = ""
LAC = ""

COUNT = 0
WAITTIME = 1
TIMEOUT = 1000

# DIODE BLINK
led = machine.Pin("LED", machine.Pin.OUT)
def blink():
 led.value(1)
 utime.sleep(.1)
 led.value(0)
 utime.sleep(.2)


# SIM868 CONFIGURATION
sim_d_key = 14		#GP14 (19)
uart_gsm_port = 0
uart_gsm_baute = 115200
gsm_module = machine.UART(uart_gsm_port, uart_gsm_baute)
print(gsm_module)


# POWER ON/OFF THE MODULE
def power_on_off():
 pwr_d_key = machine.Pin(sim_d_key, machine.Pin.OUT)
 pwr_d_key.value(1)
 print('Power off')
 utime.sleep(2)
 pwr_d_key.value(0)
 print('Power on')
 utime.sleep(7)
 print('Done')
 send_at("AT+CPIN?", "OK")
 send_at("AT+CSQ", "OK")
 send_at("AT+COPS?", "OK")
 send_at("AT+CGATT?", "OK")


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


# GET BTS INFO
def get_bts_info():
 print('-----------------------------')
 global MCC, MNC, BSIC, CELLID, LAC
 send_at("AT+CENG=4,0", "OK")
 gsm_module.write(bytearray(b'AT+CENG?\r\n'))
 rec_buff = wait_resp_info()
 buff = str(rec_buff)
 parts = buff.split(',')
 print(parts)
 if (parts[0] != "b''"):
  if (parts[0] == "b'AT+CENG?\\r\\r\\n+CENG: 4"):
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
  power_on_off()
#####################  DEFINITION OF FUNCTIONS  #####################
#####################################################################
#power_on_off()


#####################################################################
######################### GET THE BTS INFO ##########################
while True:
 try:
  if (COUNT < WAITTIME):
   COUNT+=1
   blink()
  else:
   WAITTIME = (random.randint(20, 35))
   print('Waittime: '+str(WAITTIME))
   COUNT = 0

   blink()
   get_bts_info()
   CHARNR = 0
   for CHAR in CELLID:
    CHARNR+=1
   if (CHARNR == 4 ): CELLID = '0'+CELLID
   if (CHARNR == 3 ): CELLID = '00'+CELLID
   if (CHARNR == 2 ): CELLID = '000'+CELLID
   if (CHARNR == 1 ): CELLID = '0000'+CELLID
  
   print('-----------------------------')
   print('MCC:    ' + MCC)
   print('MNC:    ' + MNC)
   print('BSIC:   ' + BSIC)
   print('CID:    ' + CELLID)
   print('LAC:    ' + LAC)
   print('-----------------------------')

   print('Sending via LORA')
   URL=DEVICE+';'+MCC+';'+MNC+';'+BSIC+';'+CELLID+';'+LAC
   print(URL)
   sx.send(b''+URL)
   print('Done\n')


######################### GET THE BTS INFO ##########################
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
