from sx1262 import SX1262
from machine import Pin, WDT, ADC
import utime, time, dht, ubinascii, network, random, socket


############### VARIABLES ###############
# LoRa_SX1262
sx = SX1262(spi_bus=1, clk=10, mosi=11, miso=12, cs=3, irq=20, rst=15, gpio=2)
sx.begin(freq=868, bw=500.0, sf=12, cr=8, syncWord=0x12,
 power=-5, currentLimit=60.0, preambleLength=8,
 implicit=False, implicitLen=0xFF,
 crcOn=True, txIq=False, rxIq=False,
 tcxoVoltage=1.7, useRegulatorLDO=False, blocking=True)

# LED indicator on Raspberry Pi Pico
led = machine.Pin("LED", machine.Pin.OUT)					#GP25/LED
led.value(0)


#WatchDog
#wdt=WDT(timeout=8300)


# MY ID
my_id = ubinascii.hexlify(machine.unique_id()).decode()


# BATTERY STATUS
analogIn = ADC(26)


# CPU TEMPERATURE
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)


# BTS
NOSIGNAL = 1
MCC = ""
MNC = ""
BSIC = ""
CELLID = ""
LAC = ""


# BUTTON CHECK
sim_d_key = machine.Pin(14, machine.Pin.OUT)						#GP14 (19)
sim_u_key = machine.Pin(17, machine.Pin.OUT)						#GP17 (22)


# UART SETTINGS
uart = machine.UART(0, 115200)


# INTERNET
TIMEOUT = 800
############### VARIABLES ###############


############### FUNCTIONS ###############
# BLINK
def blink():
 led.value(1)
 time.sleep(.2)
# wdt.feed()
 led.value(0)
 time.sleep(.8)

# SEND AT COMMAND
def send_at(cmd, back, timeout=TIMEOUT):
 blink()
 rec_buff = b''
 uart.write((cmd+'\r\n').encode())
 prvmills = utime.ticks_ms()
 while (utime.ticks_ms()-prvmills) < timeout:
  if uart.any():
   rec_buff = b"".join([rec_buff, uart.read(1)])
 if rec_buff != '':
  if back not in rec_buff.decode():
   print(cmd + ' back:\t' + rec_buff.decode())
   return 0
  else:
   print(rec_buff.decode())
   return 1
 else:
  print(cmd + ' no responce')


# WAIT RESPONSE INFO
def wait_resp_info(timeout=TIMEOUT):
 blink()
 prvmills = utime.ticks_ms()
 info = b""
 while (utime.ticks_ms()-prvmills) < timeout:
  if uart.any():
   info = b"".join([info, uart.read(1)])
 return info


# WAKEUP SIM868
def modem_online():
 if send_at("AT+CGREG?", "0,1") == 0:
  print('SIM868 is offline\r\n')
  sim_d_key.value(1)
  sim_u_key.value(0)
  utime.sleep(1)
  sim_d_key.value(0)
  sim_u_key.value(1)
  utime.sleep(3)
  print('Modem wakeup started')
  send_at("AT+CGREG?", "0,1")
############### FUNCTIONS ###############


############### MAIN PROGRAM ###############
while True:
  send_at("AT+CENG=4,0", "OK")
  uart.write(bytearray(b'AT+CENG?\r\n'))
  rec_buff = wait_resp_info()
  buff = str(rec_buff)
  parts = buff.split(',')
  if (parts[0] != "b''"):
   MCC = parts[5]
   MNC = parts[6]
   BSIC = parts[7]
   CELLIDhex = parts[8]
   CELLIDdec = int(CELLIDhex, 16)
   CELLID = str(CELLIDdec)
   LAC = parts[9]
  else:
   NOSIGNAL -= 1
   MCC = "0"
   MNC = "0"
   BSIC = "0"
   CELLID = "0"
   LAC = "0"
   
  print('Counter :'+str(NOSIGNAL))
  if (NOSIGNAL == 0):
   modem_online()
   NOSIGNAL = 10


# READ DATA FROM SENSORS
  reading = sensor_temp.read_u16() * conversion_factor 
  cputemp = str(round(27 - (reading - 0.706)/0.001721,2))

  sensorValue = analogIn.read_u16()
  voltage = round(sensorValue * (3.3 / 65535),2)
  voltage_per = round(voltage / 1.365 * 100,0)


# PUBLISH DATA VIA LORA
  sx.send(b''+str(my_id)+';'+str(MCC)+';'+str(MNC)+';'+str(BSIC)+';'+str(CELLID)+';'+str(LAC)+';'+str(cputemp)+';'+str(voltage_per))
  print("Sent: " + str(my_id)+";"+str(MCC)+";"+str(MNC)+";"+str(BSIC)+";"+str(CELLID)+";"+str(LAC)+";"+str(cputemp)+";"+str(voltage_per))
