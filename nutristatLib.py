# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 14:47:39 2020

@author: mclea
"""
#This is the delivery speed in ml/sec
deliv_Speed = 0.042

#This is a dictionary of default values. This is only used the very first time
#The script is run on a new computer. It is used to create default values for the
#"NutristatRunFile.csv". This will prevent any errors when looking for a runfile
#that doesn't already exist. NOTE: it is critical to leave the LastAction as 'END'
#in this defaultDict. All other values can be changed without issue. 
defaultDict = {'Experiment_Name_TextEdit' : '',
               'Emails_TextEdit' : 'your_email@gmail.com',
               'Number_of_Vessels_Dropdown' : '64',
               'Operating_Volume_TextEdit' : '70',
               'Sampling_Volume_TextEdit' : '5',
               'Sampling_Frequency_Day_TextEdit' : '4', 
               'Glucose_Setpoint_TextEdit' : '111',
               'Nitrite_Setpoint_TextEdit' : '10',
               'Glucose_Max_Diff_TextEdit' : '5',
               'Nitrite_Max_Diff_TextEdit' :  '0.5',
               'Glucose_Source_Concentration' : '1110',
               'Nitrite_Source_Concentration' : '100',
               'Libelium_Dropdown' : 'COM2',
               'Nitrite_Dropdown' : 'port1', 
               'Nitrate_Dropdown' : 'port2', 
               'Ammonium_Dropdown' : 'port3', 
               'pH_Dropdown' : 'port4',
               'Relays_Dropdown' : 'COM2', 
               'Delivery_Servos_Dropdown' : 'COM2', 
               'Sampling_Servos_Dropdown' : 'COM2', 
               'CO2_Dropdown' : 'COM2', 
               'DO_Dropdown' : 'COM2' ,
               'Liquid_Flow_Meter_Dropdown' : 'COM2',
               'Glucose_Intranet_IP_TextEdit' : '192.168.1.122',
               'Website_ServerIP_TextEdit' : '192.168.1.122',
               'Website_Server_Username_TextEdit' : 'tempUser',
               'Website_Server_Password_TextEdit' : 'tempPassword',
               'LastAction' : 'END'}

#List of functions for Nutristat Control
#Function sends error report for 
def send_Error(error):
      smtp_server = '64.233.184.108'
      #port = 465
      password = 'Chlamyballs2015!'
      context = ssl.create_default_context()
      sender_email = 'homnutristat@gmail.com'
      receiver_email = paramDict.get('Emails_TextEdit')
      server = smtplib.SMTP(smtp_server)
      server.ehlo()
      server.starttls()
      server.login(sender_email, password)
      server.sendmail(sender_email, receiver_email, error)
      server.quit()
      
#Function for identifying the servo positions based off of a sample position
def find_Position(vessel):
      L3V = [0,0]
      L2V = [0,0]
      L1V = [0,0]
    
      vessel = vessel - 1
      L3V[0] = vessel % 4
      vessel = vessel // 4
      L2V[0] = vessel % 4
      vessel = vessel // 4
      L1V[0] = vessel % 4
    
      L1V[1] = 0
      L2V[1] = L1V[0] + 1
      L3V[1] = L2V[0] + (L2V[1] * 4) + 1
    
#      print("L1: Set %d | Pos %d   \nL2: Set %d | Pos %d  \nL3: Set %d | Pos %d" % 
#          (L1V[1], L1V[0], L2V[1], L2V[0], L3V[1], L3V[0]))
      return [L1V, L2V, L3V]

#Function will open the correct servo motors when a vessel number and either 'Delivery'
#or 'Sampling' is provided. For the layout and wiring of servo motors, see manual      
def open_Servo(vessel, input_Output):
      #Initializes the 5 positions of the servo motor
      valvePosList = [4100, 5100, 6000, 6900, 7600]
      speed = 30
      position = find_Position(int(vessel))
      try:
            if input_Output == 'Delivery':
                  for i in range(3):
                      delivery_COM.setSpeed(position[i][1], speed)
                      delivery_COM.setTarget(position[i][1], valvePosList[position[i][0]])
                      delivery_COM.close()
            elif input_Output == 'Sampling':
                  for i in range(3):
                      sampling_COM.setSpeed(position[i][1], speed)
                      sampling_COM.setTarget(position[i][1], valvePosList[position[i][0]])
                      sampling_COM.close()                
      except ValueError:
            error = """\
            Subject: Nutristat Warning System

            There is a problem with the open_Servo function.
            Check to see if the comPort has changed or been disconnected."""
            send_Error(error)

#Function opens up the servo motor designated for the delivery medium. Currently,
#the code is written to alternate between a glucose, nitrite, or closed setting
#This function assumes that this servo is wired to position 23 on the 'delivery'
#servo pcb
def source_Delivery_Servo(gluorNO2):
      speed = 30 
      if gluorNO2 == 'glucose':
            position = 4100
            delivery_COM.setSpeed(23,speed)
            delivery_COM.setTarget(23, position)
            delivery_COM.close()
      elif gluorNO2 == 'nitrite':
            position = 5100
            delivery_COM.setSpeed(23,speed)
            delivery_COM.setTarget(23, position)
            delivery_COM.close()
      elif gluorNO2 == 'close':
            position = 7550
            delivery_COM.setSpeed(23,speed)
            delivery_COM.setTarget(23, position)
            delivery_COM.close()

#This function is meant to flush the sample line with 2 ml of nanopure prior 
#to sampling. The nanopure line should be plumbed in just before the sensors 
#on the common sampling line and the servo should be wired into position 23 
#of the 'sampling' servo pcb. For more information about plumbing, see manual for 
#additional information
def clean_Sampling():
      speed = 30
      sampling_COM.setSpeed(23, speed)
      sampling_COM.setTarget(23, 5100)
      sampling_COM.close()
      open_Relay('Sampling')
      time.sleep(48)
      closeAll_Relays()
      sampling_COM.setSpeed(23, speed)
      sampling_COM.setTarget(23, 4100)
      sampling_COM.close()
          
#Function to close all relays. It must received a command specifying whether it
#is supposed to the 'Delivery' or 'Sampling' servos
def closeAll_Servos(input_Output):
      speed = 30
      try:
            if input_Output == 'Delivery':
                  for i in range(23):
                        delivery_COM.setSpeed(i, speed)
                        delivery_COM.setTarget(i, 7550)
                        delivery_COM.close()
            elif input_Output == 'Sampling':
                  for i in range(23):
                        sampling_COM.setSpeed(i, speed)
                        sampling_COM.setTarget(i, 7550)
                        sampling_COM.close()
      except ValueError:
            error = """\
            Subject: Nutristat Warning System

            There is a problem with the closeAll_Servos function.
            Check to see if the comPort has changed or been disconnected."""
            send_Error(error)  
                         
#Function to close all relays
def closeAll_Relays():
      try:
            ser = serial.Serial(paramDict.get('Relays_Dropdown'))
            ser.write(("relay writeall" + " " + "00" + "\r").encode("ascii"))
            ser.close()
      except ValueError:
            error = """\
            Subject: Nutristat Warning System

            There is a problem with the closeAll_Relays function.
            Check to see if the comPort has changed or been disconnected."""
            send_Error(error) 
            
#Function to turn the delivery or sampling relay on. Needs to be supplied with 
#'Sampling' or 'Delivery' as an input
def open_Relay(input_Output):
      try:
            ser = serial.Serial(paramDict.get('Relays_Dropdown'))
            if input_Output == 'Sampling':
                  ser.write(('relay on ' + '1' + '\r').encode('ascii'))
                  ser.close()
            elif input_Output == 'Delivery':
                  ser.write(('relay on ' + '2' + '\r').encode('ascii'))
                  ser.close()
      except ValueError:
            error = """\
            Subject: Nutristat Warning System

            There is a problem with the open_Relay function.
            Check to see if the comPort has changed or been disconnected."""
            send_Error(error)  
            
#Function to sample a particular vessel for a preset amount of time
def sample_Vessel(vessel):
      last_Action = vessel + 'S'
      #Determines the amount of time it takes to sample a vessel based on the 
      #volume specified on the 'Experiment Setup' page. This assumes we are using
      #The initial set up which pumps at 0.042 ml/sec
      sample_Time = float(paramDict.get('Sampling_Volume_TextEdit')) / deliv_Speed
      paramDict.update(LastAction = last_Action)
      runFileDF = pd.DataFrame.from_dict(paramDict)
      runFileDF.to_csv('NutristatRunFile.csv', index=False)
      #Open the servos to the appropriate vessel
      open_Servo(vessel, 'Sampling')
      #Turn on relay to turn on sampling pump
      open_Relay('Sampling')
      time.sleep(sample_Time)
      closeAll_Relays()
      closeAll_Servos('Sampling')

#Function to deliver nutrients to a particular vessel for the amount of time
#determined by the takeAll_Measurements() function
def deliver_Vessel(vessel, no2_Volume, glu_Volume):
      last_Action = vessel + 'D'
      paramDict.update(LastAction = last_Action)
      runFileDF = pd.DataFrame.from_dict(paramDict)
      runFileDF.to_csv('NutristatRunFile.csv', index=False)
      #Open servo to glucose source if necessary
      if glu_Volume > 0.0:
            source_Delivery_Servo('glucose')
            #Open the servos to the appropriate vessel
            open_Servo(vessel, 'Delivery')
            #Turn on relay to turn on sampling pump
            open_Relay('Delivery')
            delivery_Time = glu_Volume / deliv_Speed
            time.sleep(delivery_Time)
            closeAll_Relays()
            source_Delivery_Servo('close')
      if no2_Volume > 0.0:
            source_Delivery_Servo('nitrite')
            #Open the servos to the appropriate vessel
            open_Servo(vessel, 'Delivery')
            #Turn on relay to turn on sampling pump
            open_Relay('Delivery')
            delivery_Time = no2_Volume / deliv_Speed
            time.sleep(delivery_Time)
            closeAll_Relays()
            source_Delivery_Servo('close')
            closeAll_Servos('Delivery')
      closeAll_Servos('Delivery')

#Measure the DO sensor
def readDO_Sensor():
      global vessel_DO
      comPort = paramDict.get('DO_Dropdown')
      try:
            ser = serial.Serial(comPort, 9600)
            s = ser.read(5)
            value = str(s)
            vessel_DO = float(value[2:6])
    
      except ValueError:
            vessel_DO = 'NA'
            error = """\
            Subject: Nutristat Warning System

            There is a problem with the readDO_Sensor function.
            Check to see if the comPort has changed or been disconnected."""
            send_Error(error) 
            
      finally:
            ser.close()

#Measures the CO2 sensor
def readCO2_Sensor():
      global co2_levels
      try:
            comPort = paramDict.get('CO2_Dropdown')
            ser = serial.Serial(comPort)
            ser.flushInput()
            time.sleep(1)
            ser.write(bytearray([0xFE, 0x44, 0x00, 0x08, 0x02, 0x9F, 0x25]))
            time.sleep(.01)
            response = ser.read(7)
            high = response[3]
            low = response[4]
            co2_levels = (high*256) + low
            
      except ValueError:
            co2_levels = 'NA'
            error = """\
            Subject: Nutristat Warning System

            There is a problem with the readCO2_Sensor function.
            Check to see if the comPort has changed or been disconnected."""
            send_Error(error)
      finally:
            ser.close()  

#Function to obtain glucose measurements from the citSens sensor.
#This function is different from all of the other read sensor functions as the 
#CitSens computer will be continuing measuring samples and this function updates
#the local pyMongo DB from the SQL DB located on the CitSens machine. Then we
#get the most recent measurement added to the                          
def readGlucose_DB():
      global glucose
      #Configuration for logging into CitSens bio SQLDB for glucose     
      config = {'user': 'root',
                'password': 'zomofi',
                'host': paramDict.get('Intranet_IP'),
                'database': 'biosensdb',
                'raise_on_warnings': True}
      try:
            cnx = mysql.connector.connect(**config)
            cursor = cnx.cursor() 
            query = ("SELECT timeStamp, biosensor, experimentsID, glValue, naValue  FROM experiments ORDER BY timeStamp DESC LIMIT 1")
            cursor.execute(query)
            for i in cursor:
                  glu_Time = i[0]
                  difference = glu_Time - datetime.now()
                  #If there is still an error with this function. 1) Ensure that the CitSens
                  #has taken a recent measurement since you have started your testing
                  #and 2) if it is still not working and a measurement has been taken within
                  #5 min, there is something wrong with the distance equation above
                  #If this function works at testing, please delete this note.
                  if timedelta(minutes=-5) <= difference <= timedelta(minutes=5):
                        glucose = i[3]
                  else:
                       error = """\
                       Subject: Nutristat Warning System
                       
                       There is a problem with the readGlucose_DB function.
                       It looks like the date generated by the CitSens glucose computer is not
                       within 5 minutes of the local time on the nutristat desktop.
                       This could simply be due to the computers' times not being synced or
                       it could be because the CitSens bio computer is no longer taking
                       glucose measurements."""
                       send_Error(error)  
            cursor.close()
            cnx.close()
      except mysql.connector.Error as err:
            glucose = 'NA'
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                  error = """\
                  Subject: Nutristat Warning System

                  There is a problem with the readGlucose_DB function.
                  It looks like there is something wrong with the username or
                  password for logging into the CitSensBio mySQL DB."""
                  send_Error(error) 
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                  error = """\
                  Subject: Nutristat Warning System

                  There is a problem with the readGlucose_DB function.
                  It looks like the CitSensBio mySQL DB you are looking for
                  does not exist."""
                  send_Error(error)
            else:
                  print(err)
      else:
            cnx.close() 
          
#Function for taking all measurements from the libelium sensor
#Notice that you must plug the probes into the appropriate socket according to 
#how they are hardcoded into the libelium .pde code. We aim to make this dynamic
#in the future. For now: use the following Key:
            #Socket 1: Nitrite
            #Socket 2: Nitrate
            #Socket 3: pH
            #Socket 4: Ammonium            
def readAll_Libelium_Measurements():
      global nitrite, nitrate, ammonium, ph, temp
      try:
            comPort = paramDict.get('Libelium_Dropdown')
            ser = serial.serial(comPort, 115200)
            s = ser.read_until(b'\r')
            value = str(s)
            value = value.split("\\n")

            for line in value:
                  if 'Nitrite' in line:
                        nitrite = float(line[9:])
                  else:
                        nitrite = 'NA'
                  if 'Nitrate' in line:
                        nitrate = float(line[9:])
                  else:
                        nitrate = 'NA'
                  if 'Ammonium' in line:
                        ammonium = float(line[10:])
                  else:
                        ammonium = 'NA'
                  if 'pH' in line:
                        ph = float(line[4:])
                  else:
                        ph = 'NA'
                  if 'Temp' in line:
                        temp = float(line[6:])
                  else:
                        temp = 'NA'
      except ValueError:
            error = """\
            Subject: Nutristat Warning System

            There is a problem with the readAll_Libelium_Measurements function.
            Check to see if the comPort has changed or been disconnected."""
            send_Error(error)
      finally:
            ser.close()  
            
#Should make a data deposit function so that everything is deposited under the 
#Same row in the database
#To do so just return variables and then call the variables in the final function
def deposit_Nutrient_Data(vessel):
      vesselName =  "Vessel " + str(vessel)                       
      client = MongoClient()
      db = client.Nutristat_Experiments
      collection1 = db.all_Data  
      nutrient_data = {
                  'Time': time.asctime(time.localtime()),
                  'ComputerTime': time.mktime(time.localtime()),
                  'Experiment' : paramDict.get('Experiment'),
                  'Vessel' : vesselName,
                  'CO2 Level' : co2_levels,
                  'Temperature' : temp,
                  'pH Level' : ph,
                  'DO Level' : vessel_DO,
                  'Nitrite Level' : nitrite,
                  'Nitrate Level' : nitrate,
                  'Ammonium Level' : ammonium,
                  'Glucose Level' : glucose,
                  'Action' : action,
                  'Volume NO2 Delivered' : no2_Volume,
                  'Volume Glucose Delivered' : glu_Volume
                  }
      collection1.insert_one(nutrient_data)
#Function that will call all of the individual measurement functions      
def takeAll_Measurements():
      #Wait 5 min for measurements to settle out
      time.sleep(120)
      #measure CO2
      readCO2_Sensor()
      #measure Glucose
      readGlucose_DB()
      #measure all libelium analytes (pH, nitrite, nitrate, ammonia, temp)
      readAll_Libelium_Measurements()
      #measure DO
      readDO_Sensor()

#Determines whether or not  
      ####MAKE SURE TO ADD THE APPEND VESSEL NAME AND DELIVERY OR SAMPLING TO 
      #THE CSV FILE AT THIS POINT
      
def check_Measurements(vessel):
      global action, no2_Volume, glu_Volume
      sample_Volume = float(0)
      finalVolume = float(paramDict.get('Operating_Volume_TextEdit'))
      #Define variables for nitrite
      no2 = float(nitrite)
      no2Set = float(paramDict.get('Nitrite_Setpoint_TextEdit'))
      no2Stock = float(paramDict.get('Nitrite_Source_Concentration'))
      no2maxDiff = float(paramDict.get('Nitrite_Max_Diff_TextEdit'))
      #Define variables for glucose
      glu = float(glucose)
      gluSet = float(paramDict.get('Glucose_Setpoint_TextEdit'))
      gluStock = float(paramDict.get('Glucose_Source_Concentration'))
      glumaxDiff = float(paramDict.get('Glucose_Max_Diff_TextEdit'))
      #Check Glucose values
      gluDiff = glu - gluSet            
      if  gluDiff <= -1 * glumaxDiff:
            glu_Volume = ((gluSet * finalVolume - ((finalVolume - sample_Volume)
            * glu))/(gluStock - glu))
            #This corrects for glucose additions as glucose stock medium will 
            #contain nitrite at the setpoint concentration and glucose will be added
            #first if both nutrients need to be added
            no2 = ((no2 * finalVolume) + (no2Set * glu_Volume)) / finalVolume
      else:
            glu_Volume = 0.0
            
      #Check Nitrite values
      no2Diff = no2 - no2Set            
      if  no2Diff <= -1 * no2maxDiff:
            no2_Volume = ((no2Set * finalVolume - ((finalVolume - sample_Volume)
            * no2))/(no2Stock - no2))
      else:
            no2_Volume = 0.0
            
      if no2_Volume == 0.0 and glu_Volume == 0.0:
            action = 'No Delivery'
      elif no2_Volume > 0.0 and glu_Volume > 0.0:
            action = 'NO2&GLU'
      elif no2_Volume > 0.0 and glu_Volume == 0.0:
            action = 'NO2'
      elif no2_Volume == 0.0 and glu_Volume > 0.0:
            action = 'GLU'
      else:
            action = 'error'
            error = """\
                  Subject: Nutristat Warning System

                  There is a problem with the check_Measurements function.
                  This is being generated because one or more of the volumes 
                  that we have chosen to deliver to the system are likely negative.
                  This could be due to an error in the quantification of nitrite
                  and/or glucose. Check the raw data coming out of the sensors
                  to see if one or both appear suspicious and see if it is a connection
                  issue or a calibration issue."""
            send_Error(error)
            
def mainLoop(status):
      thread = threading.Thread(target=init_input_timer,daemon=True)
      thread.start() 
      global vesselArray
      vesselArray = []
      if status == 'NEW':
            newDict = {'Experiment_Name_TextEdit' : Experiment_Name_TextEdit,
               'Emails_TextEdit' : Emails_TextEdit,
               'Number_of_Vessels_Dropdown' : Number_of_Vessels_Dropdown,
               'Operating_Volume_TextEdit' : Operating_Volume_TextEdit,
               'Sampling_Volume_TextEdit' : Sampling_Volume_TextEdit,
               'Sampling_Frequency_Day_TextEdit' : Sampling_Frequency_Day_TextEdit, 
               'Glucose_Setpoint_TextEdit' : Glucose_Setpoint_TextEdit,
               'Nitrite_Setpoint_TextEdit' : Nitrite_Setpoint_TextEdit,
               'Glucose_Max_Diff_TextEdit' : Glucose_Max_Diff_TextEdit,
               'Nitrite_Max_Diff_TextEdit' :  Nitrite_Max_Diff_TextEdit,
               'Glucose_Source_Concentration' : Glucose_Source_Concentration,
               'Nitrite_Source_Concentration' : Nitrite_Source_Concentration,
               'Libelium_Dropdown' : Libelium_Dropdown,
               'Nitrite_Dropdown' : Nitrite_Dropdown, 
               'Nitrate_Dropdown' : Nitrate_Dropdown, 
               'Ammonium_Dropdown' : Ammonium_Dropdown, 
               'pH_Dropdown' : pH_Dropdown,
               'Relays_Dropdown' : Relays_Dropdown, 
               'Delivery_Servos_Dropdown' : Delivery_Servos_Dropdown, 
               'Sampling_Servos_Dropdown' : Sampling_Servos_Dropdown, 
               'CO2_Dropdown' : CO2_Dropdown, 
               'DO_Dropdown' : DO_Dropdown ,
               'Liquid_Flow_Meter_Dropdown' : Liquid_Flow_Meter_Dropdown,
               'Glucose_Intranet_IP_TextEdit' : Glucose_Intranet_IP_TextEdit,
               'Website_ServerIP_TextEdit' : Website_ServerIP_TextEdit,
               'Website_Server_Username_TextEdit' : Website_Server_Username_TextEdit,
               'Website_Server_Password_TextEdit' : Website_Server_Password_TextEdit,
               'LastAction' : 'NEW'}
            #Sampling interval in seconds based on the user input of daily sampling
            #sampling frequency
            paramDict.update(newDict)
            for i in range(1,int(paramDict.get('Number_of_Vessels_Dropdown'))+1):
                  vesselArray.append(str(i))
            sampleInterval = 24 / int(paramDict.get('Sampling_Frequency_Day_TextEdit')) * 3600                  
            while True:
                  startLoop = time.time()
                  for i in vesselArray:
                        sample_Vessel(i)
                        takeAll_Measurements()
                        check_Measurements(i)
                        clean_Sampling()
                        deposit_Nutrient_Data(i)
                        deliver_Vessel(i, no2_Volume, glu_Volume)
                  waitTime = (sampleInterval - (time.time() - startLoop))                  
                  time.sleep(waitTime)
      elif status == 'Interrupt':
            sampleInterval = 24 / int(paramDict.get('Sampling_Frequency_Day_TextEdit')) * 3600
            #Generates the full sample array based on the old paramDict dictionary
            #declared in the main loop 
            for i in range(1,int(paramDict.get('Number_of_Vessels_Dropdown'))+1):
                  vesselArray.append(str(i))
            #Finds the most recent vessel based on the "NutristatRunFile.csv"
            ves = int(paramDict.get('LastAction')[:-1])
            tempArray = []
            #Creates an array that will finish up where the previous sampling
            #Loop left off. This array will only be run through once and then 
            #a new while loop will be started that will act as usual
            for i in range(ves,int(paramDict.get('Number_of_Vessels_Dropdown'))+1):
                  tempArray.append(str(i))
            #All of the main actions for the
            for i in tempArray:
                  sample_Vessel(i)
                  takeAll_Measurements()
                  check_Measurements(i)
                  clean_Sampling()
                  deposit_Nutrient_Data(i)
                  deliver_Vessel(i, no2_Volume, glu_Volume)
            client = MongoClient()
            db = client.Nutristat_Experiments
            collection1 = db.all_Data
            #Collects all of the data for Vessel 1 from the current experiment
            query = {'$and':[{'Vessel': 'Vessel 1'},{'Experiment': paramDict.get('Experiment')}]}
            #Collects the most recent measurement from this query
            recentMeasurement = collection1.find(query).limit(1).sort([('$natural',-1)])
            for i in recentMeasurement:
                  firstSampleTime = i['ComputerTime']
            waitTime = (sampleInterval - (time.time() - firstSampleTime))
            if waitTime <= 0:
                  while True:
                        startLoop = time.time()
                        for i in vesselArray:
                              sample_Vessel(i)
                              takeAll_Measurements()
                              check_Measurements(i)
                              clean_Sampling()
                              deposit_Nutrient_Data(i)
                              deliver_Vessel(i, no2_Volume, glu_Volume)
                        waitTime = (sampleInterval - (time.time() - startLoop))                  
                        time.sleep(waitTime)
            elif waitTime > 0:
                  time.sleep(waitTime)
                  while True:
                        startLoop = time.time()
                        for i in vesselArray:
                              sample_Vessel(i)
                              takeAll_Measurements()
                              check_Measurements(i)
                              clean_Sampling()
                              deposit_Nutrient_Data(i)
                              deliver_Vessel(i, no2_Volume, glu_Volume)
                        waitTime = (sampleInterval - (time.time() - startLoop))                  
                        time.sleep(waitTime)
            
            
            
            
            
            
            