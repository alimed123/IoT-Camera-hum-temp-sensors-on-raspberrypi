
import time
import board
import adafruit_shtc3
from datetime import datetime
from pymongo import MongoClient
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import RPi.GPIO as GPIO  # Make sure to import the GPIO library
import os
port = 587  # For starttls
sender_email = "notificationsgreenhouse@gmail.com"
password = "hedzov-0cusvy-foxVuz"
subject = 'DHT reader is down'
body = 'Hello, DHT reader is down please check connections'

# Prepare the email
msg = MIMEMultipart("alternative")
msg["From"] = sender_email
msg['To'] = "alisaboundji2003@gmail.com"
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain'))



def init_sensor():
    i2c = board.I2C()  # Create a new I2C bus
    return adafruit_shtc3.SHTC3(i2c)

sensor_rpi = init_sensor()
# MongoDB setup
client = MongoClient('mongodb+srv://greenhousedashboarduser:x0uJC6yjWd41d88d@cluster0.xoiyjzk.mongodb.net/?retryWrites=true&w=majority')
db =client['sensorcollection']  # Database name
collection = db['every5minutedata2']  # Collection name


# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(17, GPIO.OUT)
GPIO.output(18, GPIO.HIGH)
GPIO.output(17, GPIO.HIGH)

def read_rpi_sensor():
    try:
        temperature, humidity = sensor_rpi.measurements
        return temperature, humidity
    except:
        try:
            temperature, humidity = sensor_rpi.measurements
            return temperature, humidity
        except Exception as e:
            print("Error")
            print(e)

def reinitialize_sensor():
    try:
        i2c = board.I2C()  # Reinitialize I2C interface
        sensor = adafruit_shtc3.SHTC3(i2c)
        return sensor
    except Exception as e:
        print(f"Failed to reinitialize I2C sensor: {e}")
        return None


def send_data_to_mongodb(temperature, humidity):
    document = {
        "timestamp": datetime.now().isoformat(),
        "temperature": round(temperature, 1),
        "humidity": round(humidity, 1)
    }
    collection.insert_one(document)
    print("Data sent to MongoDB:", document)


if __name__ == "__main__":
  try:
      while True:
          try:
              i = 0
              # Read from Raspberry Pi sensor
              temp_rpi, hum_rpi = read_rpi_sensor()

              if temp_rpi is not None and hum_rpi is not None and (0 <= hum_rpi <= 100) and (-40 <= temp_rpi <= 80):
                  send_data_to_mongodb(temp_rpi,hum_rpi)
                  print(f"original i2c sensor read -> Raspberry Pi - Temperature: {temp_rpi:.1f} C, Humidity: {hum_rpi:.1f}%")
              else:
                  while temp_rpi is None or hum_rpi is None or not (0 <= hum_rpi <= 100) or not (-40 <= temp_rpi <= 80):
                      i+=1
                      GPIO.output(17, GPIO.LOW)  # Set GPIO 17 to HIGH
                      time.sleep(0.5)
                      GPIO.output(18, GPIO.LOW)  # Set GPIO 4 to HIGH
                      time.sleep(0.5)
                      temp_rpi, hum_rpi = read_rpi_sensor()
                      GPIO.output(17, GPIO.LOW)  # Set GPIO 17 to LOW
                      time.sleep(0.5)
                      GPIO.output(18, GPIO.LOW)  # Set GPIO 4 to LOW
                      time.sleep(0.5)
                      if temp_rpi is not None and hum_rpi is not None and (0 <= hum_rpi <= 100) and (-40 <= temp_rpi <= 80):
                          send_data_to_mongodb(temp_rpi,hum_rpi)
                          print(f"Alternate i2c sensor read -> Raspberry Pi - Temperature: {temp_rpi:.1f} C, Humidity: {hum_rpi:.1f}%")
                          break
                      else:
                          if i == 2:
                              try:
                                  server = smtplib.SMTP('smtp.gmail.com', 587)
                                  server.starttls()  # Secure the connection
                                  server.login(sender_email, gmail_password)
                                  text = msg.as_string()
                                  server.sendmail(gmail_user, to, text)
                                  server.quit()
                                  print("Email sent successfully!")
                                  break
                              except Exception as e:
                                  os.system("sudo reboot")
              time.sleep(300) #5*60
              sensor_rpi = init_sensor()
              
          except:
              os.system("sudo reboot")
  except Exception as e:
      print("Program terminated",e)
      os.system("sudo reboot")
      GPIO.cleanup()
