# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 14:29:44 2020

@author: mclea
"""
#Import the necessary packages
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer, QThread
from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem
import pyqtgraph as pg
from pyqtgraph.Point import Point
import numpy as np
import mysql.connector
from mysql.connector import errorcode
import sys
from pymongo import MongoClient
import pymongo
from time import mktime, time
from datetime import datetime, timedelta
import threading
import serial
import pandas as pd
import smtplib, ssl
import maestro2

#This is the main loop code for the nutristat control module
###############################################################################
#When file initially runs, it looks for the previous run file present in the current
#working directory. If this program has never run in this location before, it 
#will await user input from the GUI
try:
#This will be the def line for the main function once tested
      runFileDF = pd.read_csv('NutristatRunFile.csv')
      paramDict = dict(zip(runFileDF['Variable'], runFileDF['Value']))
      if paramDict.get('LastAction') == 'END':
            print('Waiting for user input from GUI')
      elif 'D' in paramDict.get('LastAction'):
            print('Delivery to Vessel ' + paramDict.get('LastAction')[:-1])
      elif 'S' in paramDict.get('LastAction'):
            print('Sample to Vessel ' + paramDict.get('LastAction')[:-1])
except IOError:
      print('Waiting for user input from GUI')
#Assigns Variable names. This will eventually be replaced by user input from the 
#GUI or from the template sheet created from the previous run

#This will be the def line for the main function once tested
runFileDF = pd.read_csv('NutristatRunFile.csv')
paramDict = dict(zip(runFileDF['Variable'], runFileDF['Value']))
if paramDict.get('LastAction') == 'END':
#Need to insert a function here that excepts the user input from the GUI
#Might be good to put a wait function in here
      Experiment_Name_TextEdit = 'Experiment1'
      Number_of_Vessels_Dropdown = 64 
      Sampling_Frequency_Day_TextEdit = 4 
      Glucose_Setpoint_TextEdit = 111
      Nitrite_Setpoint_TextEdit = 10
      Glucose_Max_Diff_TextEdit = 5
      Nitrite_Max_Diff_TextEdit =  0.5
      Glucose_Source_Concentration = 1110
      Nitrite_Source_Concentration = 100
      Libelium_Dropdown = 'COM2'
      Nitrite_Dropdown = 'port1' 
      Nitrate_Dropdown = 'port2' 
      Ammonium_Dropdown = 'port3' 
      pH_Dropdown = 'port4' 
      Relays_Dropdown = 'COM2' 
      Delivery_Servos_Dropdown = 'COM2' 
      Sampling_Servos_Dropdown = 'COM2' 
      CO2_Dropdown = 'COM2' 
      DO_Dropdown = 'COM2' 
      Liquid_Flow_Meter_Dropdown = 'COM2'
      Intranet_IP = '192.168.1.122'
      Glucose_Sensor_TextEdit = '50020557'
      LastAction = 'NEW'
      print('NEW')
elif 'D' in paramDict.get('LastAction'):
      print('Delivery to Vessel ' + paramDict.get('LastAction')[:-1])
elif 'S' in paramDict.get('LastAction'):
      print('Sample to Vessel ' + paramDict.get('LastAction')[:-1])
###############################################################################      
#Overview of Main Loop                                                        #
###############################################################################
### 1) Check to see the status of the previous run and assign variables
      
### 2) Sample Next Vessel
#def sample_Vessel(vessel):
      
### 3) Check to see if Glucose or Nitrite are below the required thresholds
#def check_Glucose(vessel, currentValue):
#def check_Nitrite(vessel, currentValue):
      ### 4) Deliver nutrients if necessary
      #def deliver_Vessel(vessel, volume):
      
### 5) Sample next vessel

###############################################################################      
#Class for generating real-time plots
class DateAxisItem(pg.AxisItem):
    """
    A tool that provides a date-time aware axis. It is implemented as an
    AxisItem that interpretes positions as unix timestamps (i.e. seconds
    since 1970).
    The labels and the tick positions are dynamically adjusted depending
    on the range.
    It provides a  :meth:`attachToPlotItem` method to add it to a given
    PlotItem
    """
    
    # Max width in pixels reserved for each label in axis
    _pxLabelWidth = 80

    def __init__(self, *args, **kwargs):
        pg.AxisItem.__init__(self, *args, **kwargs)
        self._oldAxis = None

    def tickValues(self, minVal, maxVal, size):
        """
        Reimplemented from PlotItem to adjust to the range and to force
        the ticks at "round" positions in the context of time units instead of
        rounding in a decimal base
        """

        maxMajSteps = int(size/self._pxLabelWidth)

        dt1 = datetime.fromtimestamp(minVal)
        dt2 = datetime.fromtimestamp(maxVal)

        dx = maxVal - minVal
        majticks = []

        if dx > 63072001:  # 3600s*24*(365+366) = 2 years (count leap year)
            d = timedelta(days=366)
            for y in range(dt1.year + 1, dt2.year):
                dt = datetime(year=y, month=1, day=1)
                majticks.append(mktime(dt.timetuple()))

        elif dx > 5270400:  # 3600s*24*61 = 61 days
            d = timedelta(days=31)
            dt = dt1.replace(day=1, hour=0, minute=0,
                             second=0, microsecond=0) + d
            while dt < dt2:
                # make sure that we are on day 1 (even if always sum 31 days)
                dt = dt.replace(day=1)
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 172800:  # 3600s24*2 = 2 days
            d = timedelta(days=1)
            dt = dt1.replace(hour=0, minute=0, second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 7200:  # 3600s*2 = 2hours
            d = timedelta(hours=1)
            dt = dt1.replace(minute=0, second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 1200:  # 60s*20 = 20 minutes
            d = timedelta(minutes=10)
            dt = dt1.replace(minute=(dt1.minute // 10) * 10,
                             second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 120:  # 60s*2 = 2 minutes
            d = timedelta(minutes=1)
            dt = dt1.replace(second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 20:  # 20s
            d = timedelta(seconds=10)
            dt = dt1.replace(second=(dt1.second // 10) * 10, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 2:  # 2s
            d = timedelta(seconds=1)
            majticks = range(int(minVal), int(maxVal))

        else:  # <2s , use standard implementation from parent
            return pg.AxisItem.tickValues(self, minVal, maxVal, size)

        L = len(majticks)
        if L > maxMajSteps:
            majticks = majticks[::int(np.ceil(float(L) / maxMajSteps))]

        return [(d.total_seconds(), majticks)]

    def tickStrings(self, values, scale, spacing):
        """Reimplemented from PlotItem to adjust to the range"""
        ret = []
        if not values:
            return []

        if spacing >= 31622400:  # 366 days
            fmt = "%Y"

        elif spacing >= 2678400:  # 31 days
            fmt = "%Y %b"

        elif spacing >= 86400:  # = 1 day
            fmt = "%b/%d"

        elif spacing >= 3600:  # 1 h
            fmt = "%b/%d-%Hh"

        elif spacing >= 60:  # 1 m
            fmt = "%H:%M"

        elif spacing >= 1:  # 1s
            fmt = "%H:%M:%S"

        else:
            # less than 2s (show microseconds)
            # fmt = '%S.%f"'
            fmt = '[+%fms]'  # explicitly relative to last second

        for x in values:
            try:
                t = datetime.fromtimestamp(x)
                ret.append(t.strftime(fmt))
            except ValueError:  # Windows can't handle dates before 1970
                ret.append('')

        return ret

    def attachToPlotItem(self, plotItem):
        """Add this axis to the given PlotItem
        :param plotItem: (PlotItem)
        """
        self.setParentItem(plotItem)
        viewBox = plotItem.getViewBox()
        self.linkToView(viewBox)
        self._oldAxis = plotItem.axes[self.orientation]['item']
        self._oldAxis.hide()
        plotItem.axes[self.orientation]['item'] = self
        pos = plotItem.axes[self.orientation]['pos']
        plotItem.layout.addItem(self, *pos)
        self.setZValue(-1000)

    def detachFromPlotItem(self):
        """Remove this axis from its attached PlotItem
        (not yet implemented)
        """
        raise NotImplementedError()  # TODO

###############################################################################
###############################################################################      
#initializing timer and data lists
dataList = []
timeList = []
timers = []
timers1 = []
#initializing collection in database
db_data = collection1.find()    

#Initializes the control of the maestro servo controller
delivery_COM = maestro2.Controller(paramDict.get('Delivery_Servos_Dropdown'))     
sampling_COM = maestro2.Controller(paramDict.get('Sampling_Servos_Dropdown'))
 
#Time it takes to sample in minutes
sample_Time = 60
#Delivery time in seconds determined by measurement step
delivery_Time = 60
   
      
      
      
      
      
      