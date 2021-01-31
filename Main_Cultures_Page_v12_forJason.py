# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Main_Cultures_Page.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer, QThread
import numpy as np
import pyqtgraph as pg
import sys
import pymongo
from pymongo import MongoClient
from time import mktime
import reading_co2_sensor
import threading
from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem
import serial
from datetime import datetime, timedelta
import time
from pyqtgraph.Point import Point
#import reading_DO_sensor

relayCOM = 'COM8'

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

#initializing database connection and information
client = MongoClient('mongodb://localhost:27017')
db = client.CO2_Sensor_Data
collection1 = db.raw_data
#initializing timer and data lists
dataList = []
timeList = []
timers = []
timers1 = []
#initializing collection in database
db_data = collection1.find()


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1127, 882)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.Tabs = QtWidgets.QTabWidget(self.centralwidget)
        self.Tabs.setGeometry(QtCore.QRect(0, 0, 1121, 881))
        self.Tabs.setObjectName("Tabs")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.Culture_Dropdown = QtWidgets.QComboBox(self.tab)
        self.Culture_Dropdown.setGeometry(QtCore.QRect(20, 350, 69, 20))
        self.Culture_Dropdown.setObjectName("Culture_Dropdown")
        self.Culture_Dropdown.addItem("")
        self.Culture_Dropdown.addItem("")
        self.Culture_Dropdown.addItem("")
        self.Culture_Dropdown.addItem("")
        self.Culture_Dropdown.addItem("")
        self.Culture_Dropdown.addItem("")
        self.Data_Table1 = QtWidgets.QTableWidget(self.tab)
        self.Data_Table1.setColumnCount(2)
        self.Data_Table1.setRowCount(1)
        #self.Data_Table1.setHorizontalHeaderLabels(["PPM" , "Time"])
        self.Data_Table1.setUpdatesEnabled(True)
        self.Data_Table1.setGeometry(QtCore.QRect(100, 80, 431, 631))
        self.Data_Table1.setObjectName("Data_Table1")
        #self.Data_Table1.setModel(QtGui.QStandardModel(0,2,self.tab))
        
        #self.Data_Table1.setWordWrap(True)
        self.Data_Table1.resizeColumnsToContents()
        self.Data_Table1.setHorizontalHeaderLabels(('Time', 'CO2 (ppm)'))
        self.Nutrient_Levels_Textbox = QtWidgets.QLabel(self.tab)
        self.Nutrient_Levels_Textbox.setGeometry(QtCore.QRect(270, 60, 81, 20))
        self.Nutrient_Levels_Textbox.setObjectName("Nutrient_Levels_Textbox")
        date_axis = DateAxisItem(orientation = 'bottom')
        self.Data_Graph = PlotWidget(self.tab, axisItems = {'bottom': date_axis})
        self.Data_Graph.setGeometry(QtCore.QRect(580, 180, 491, 481))
        self.Data_Graph.setObjectName("Data_Graph")
        self.Data_Graph.setLabel('left', 'CO2 Concentration (ppm)', color='white',size = 40)
        self.Data_Graph.setLabel('bottom', 'Seconds', color='white',size = 40)

        #starts thread for updating the plot at same time as taking in data.
        thread = threading.Thread(target=self.update_plot_timer(),daemon=True)
        thread.start()
        self.Exit_Button1 = QtWidgets.QPushButton(self.tab)
        self.Exit_Button1.setGeometry(QtCore.QRect(1030, 0, 75, 23))
        self.Exit_Button1.setObjectName("Exit_Button1")
        self.Tabs.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.Nitrite_Levels_Textbox_2 = QtWidgets.QLabel(self.tab_2)
        self.Nitrite_Levels_Textbox_2.setGeometry(QtCore.QRect(540, 710, 61, 21))
        self.Nitrite_Levels_Textbox_2.setObjectName("Nitrite_Levels_Textbox_2")
        self.Culture2_Checkbox2_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture2_Checkbox2_2.setGeometry(QtCore.QRect(240, 610, 70, 17))
        self.Culture2_Checkbox2_2.setObjectName("Culture2_Checkbox2_2")
        self.Culture4_Checkbox2_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture4_Checkbox2_2.setGeometry(QtCore.QRect(340, 580, 70, 17))
        self.Culture4_Checkbox2_2.setObjectName("Culture4_Checkbox2_2")
        self.Text_box1_2 = QtWidgets.QTextEdit(self.tab_2)
        self.Text_box1_2.setGeometry(QtCore.QRect(520, 130, 111, 31))
        self.Text_box1_2.setObjectName("Text_box1_2")
        self.Culture1_Checkbox2_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture1_Checkbox2_2.setGeometry(QtCore.QRect(240, 580, 70, 17))
        self.Culture1_Checkbox2_2.setObjectName("Culture1_Checkbox2_2")
        self.Glucose_Textbox_2 = QtWidgets.QLabel(self.tab_2)
        self.Glucose_Textbox_2.setGeometry(QtCore.QRect(300, 90, 51, 21))
        self.Glucose_Textbox_2.setObjectName("Glucose_Textbox_2")
        self.Culture6_Checkbox2_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture6_Checkbox2_2.setGeometry(QtCore.QRect(340, 640, 70, 17))
        self.Culture6_Checkbox2_2.setObjectName("Culture6_Checkbox2_2")
        self.Culture4_Checkbox1_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture4_Checkbox1_2.setGeometry(QtCore.QRect(340, 170, 70, 17))
        self.Culture4_Checkbox1_2.setObjectName("Culture4_Checkbox1_2")
        self.Data_table1_2 = QtWidgets.QTableWidget(self.tab_2)
        self.Data_table1_2.setGeometry(QtCore.QRect(500, 170, 151, 141))
        self.Data_table1_2.setObjectName("Data_table1_2")
        self.Data_table1_2.setColumnCount(2)
        self.Data_table1_2.setRowCount(1)
        self.Text_box2_2 = QtWidgets.QTextEdit(self.tab_2)
        self.Text_box2_2.setGeometry(QtCore.QRect(520, 520, 111, 31))
        self.Text_box2_2.setObjectName("Text_box2_2")
        self.Culture5_Checkbox1_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture5_Checkbox1_2.setGeometry(QtCore.QRect(340, 200, 70, 17))
        self.Culture5_Checkbox1_2.setObjectName("Culture5_Checkbox1_2")
        self.Culture3_Checkbox1_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture3_Checkbox1_2.setGeometry(QtCore.QRect(240, 230, 70, 17))
        self.Culture3_Checkbox1_2.setObjectName("Culture3_Checkbox1_2")
        self.Culture6_Checkbox1_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture6_Checkbox1_2.setGeometry(QtCore.QRect(340, 230, 70, 17))
        self.Culture6_Checkbox1_2.setObjectName("Culture6_Checkbox1_2")
        self.Deposit_Button1_2 = QtWidgets.QPushButton(self.tab_2)
        self.Deposit_Button1_2.setGeometry(QtCore.QRect(640, 130, 75, 23))
        self.Deposit_Button1_2.setObjectName("Deposit_Button1_2")
        self.Culture2_Checkbox1_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture2_Checkbox1_2.setGeometry(QtCore.QRect(240, 200, 70, 17))
        self.Culture2_Checkbox1_2.setObjectName("Culture2_Checkbox1_2")
        self.Nitrite_Textbox_2 = QtWidgets.QLabel(self.tab_2)
        self.Nitrite_Textbox_2.setGeometry(QtCore.QRect(300, 500, 51, 21))
        self.Nitrite_Textbox_2.setObjectName("Nitrite_Textbox_2")
        self.Culture5_Checkbox2_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture5_Checkbox2_2.setGeometry(QtCore.QRect(340, 610, 70, 17))
        self.Culture5_Checkbox2_2.setObjectName("Culture5_Checkbox2_2")
        self.Culture3_Checkbox2_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture3_Checkbox2_2.setGeometry(QtCore.QRect(240, 640, 70, 17))
        self.Culture3_Checkbox2_2.setObjectName("Culture3_Checkbox2_2")
        self.Deposit_Button2_2 = QtWidgets.QPushButton(self.tab_2)
        self.Deposit_Button2_2.setGeometry(QtCore.QRect(640, 520, 75, 23))
        self.Deposit_Button2_2.setObjectName("Deposit_Button2_2")
        self.Glucose_Levels_Textbox_2 = QtWidgets.QLabel(self.tab_2)
        self.Glucose_Levels_Textbox_2.setGeometry(QtCore.QRect(540, 320, 71, 21))
        self.Glucose_Levels_Textbox_2.setObjectName("Glucose_Levels_Textbox_2")
        self.Culture1_Checkbox1_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture1_Checkbox1_2.setGeometry(QtCore.QRect(240, 170, 70, 17))
        self.Culture1_Checkbox1_2.setObjectName("Culture1_Checkbox1_2")
        self.Data_table2_2 = QtWidgets.QTableWidget(self.tab_2)
        self.Data_table2_2.setGeometry(QtCore.QRect(500, 560, 151, 131))
        self.Data_table2_2.setObjectName("Data_table2_2")
        self.Data_table2_2.setColumnCount(2)
        self.Data_table2_2.setRowCount(1)
        self.Exit_Button2 = QtWidgets.QPushButton(self.tab_2)
        self.Exit_Button2.setGeometry(QtCore.QRect(1030, 0, 75, 23))
        self.Exit_Button2.setObjectName("Exit_Button2")
        self.Open_button1 = QtWidgets.QPushButton(self.tab_2)
        self.Open_button1.setGeometry(QtCore.QRect(230, 300, 75, 23))
        self.Open_button1.setObjectName("Open_button1")
        self.Close_button1 = QtWidgets.QPushButton(self.tab_2)
        self.Close_button1.setGeometry(QtCore.QRect(340, 300, 75, 23))
        self.Close_button1.setObjectName("Close_button1")
        self.Open_button2 = QtWidgets.QPushButton(self.tab_2)
        self.Open_button2.setGeometry(QtCore.QRect(230, 710, 75, 23))
        self.Open_button2.setObjectName("Open_button2")
        self.Close_button2 = QtWidgets.QPushButton(self.tab_2)
        self.Close_button2.setGeometry(QtCore.QRect(340, 710, 75, 23))
        self.Close_button2.setObjectName("Close_button2")
        self.Culture7_Checkbox1_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture7_Checkbox1_2.setGeometry(QtCore.QRect(240, 260, 70, 17))
        self.Culture7_Checkbox1_2.setObjectName("Culture7_Checkbox1_2")
        self.Culture8_Checkbox1_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture8_Checkbox1_2.setGeometry(QtCore.QRect(340, 260, 70, 17))
        self.Culture8_Checkbox1_2.setObjectName("Culture8_Checkbox1_2")
        self.Culture7_Checkbox2_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture7_Checkbox2_2.setGeometry(QtCore.QRect(240, 670, 70, 17))
        self.Culture7_Checkbox2_2.setObjectName("Culture7_Checkbox2_2")
        self.Culture8_Checkbox2_2 = QtWidgets.QCheckBox(self.tab_2)
        self.Culture8_Checkbox2_2.setGeometry(QtCore.QRect(340, 670, 70, 17))
        self.Culture8_Checkbox2_2.setObjectName("Culture8_Checkbox2_2")
        self.Tabs.addTab(self.tab_2, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1127, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.actionNew_File = QtWidgets.QAction(MainWindow)
        self.actionNew_File.setObjectName("actionNew_File")
        self.actionOpen_File = QtWidgets.QAction(MainWindow)
        self.actionOpen_File.setObjectName("actionOpen_File")
        self.actionSave_File = QtWidgets.QAction(MainWindow)
        self.actionSave_File.setObjectName("actionSave_File")
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        #gives buttons functionality
        self.Exit_Button1.clicked.connect(self.exitButton)
        self.Exit_Button2.clicked.connect(self.exitButton)
        self.Deposit_Button1_2.clicked.connect(self.update_relay)
        self.Deposit_Button2_2.clicked.connect(self.update_relay_1)
        self.Close_button1.clicked.connect(self.close_relays)
        self.Close_button2.clicked.connect(self.close_relays)
        self.Open_button1.clicked.connect(self.open_relays)
        self.Open_button2.clicked.connect(self.open_relays)
        self.retranslateUi(MainWindow)
        self.Tabs.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
    
#updates both the graph and the table with data from the database.
    def update(self):
        updateXList = []
        updateYList = []
        updateTList = []
        
        time_init = 0
        timebetweenreads = 6
        #Grabs data from current experiment from a specific vessel
        #Replace 'Vessel 1'with user input from dropdown menu you can use an array
        query = {'$and':[{'Vessel':'Vessel 1'},{'Experiment': paramDict.get('Experiment')}]}
        #Grabs data from current experiment from all vessels
        queryAllVes = {'Experiment': paramDict.get('Experiment')}
        db_vesData = collection1.find(query)
        db_allData = collection1.find(queryAllVes)
        #model = QtGui.QStandardItemModel(self.Data_Table1)
#        analyte = USERINPUT FROM TAB
        for x in db_data:
            tableData = []
            row = 0
            updateXList.append(x[analyte])
            updateYList.append(x['ComputerTime'])
            updateTList.append(x['Time'])
#            print(updateYList)
            #col = 0
            if self.Data_Table1.rowCount() < len(updateXList):
                self.Data_Table1.insertRow(row)
        for a, b in zip(updateXList, updateTList):
            col = 0
            cellData = QTableWidgetItem(str(b))
            cellData2 = QTableWidgetItem(str(a))
            self.Data_Table1.setItem(row,col,cellData)
            col += 1
            self.Data_Table1.setItem(row,col,cellData2)
            row += 1

        
        self.Data_Table1.insertRow(row)
        row += 1
        
        
            #updateYList.append(x['Time'])
            #timeList.append(time_init)
            #time_init = time_init + timebetweenreads
        #updateYList = np.arange(0, 6*len(updateXList), 6)
        self.Data_Graph.plot(updateYList,updateXList,title = "Nutrient Level Data")


#controls the relay through first set of checkboxes
    def update_relay(self):
        ser = serial.Serial(relayCOM)
        boxes = [self.Culture1_Checkbox1_2,self.Culture2_Checkbox1_2,self.Culture3_Checkbox1_2,
                 self.Culture4_Checkbox1_2,self.Culture5_Checkbox1_2,self.Culture6_Checkbox1_2,
                 self.Culture7_Checkbox1_2,self.Culture8_Checkbox1_2]
        checkedBoxes = []
        x = 0
        for i in boxes:
            if i.isChecked():
                checkedBoxes.append(x)
            x = x + 1
        for i in checkedBoxes:
            #ser.close()
            #ser = serial.Serial(relayCOM)
            ser.write(("relay on " + str(i) + "\r").encode("ascii"))

#turns off all relays
    def close_relays(self):
        ser = serial.Serial(relayCOM)
        ser.write(("relay writeall" + " " + "00" + "\r").encode("ascii"))
    
 #turns on all relays   
    def open_relays(self):
        ser = serial.Serial(relayCOM)
        ser.write(("relay writeall" + " " + "ff" + "\r").encode("ascii"))
#controls relay through second set of checkboxes.
    def update_relay_1(self):
        ser = serial.Serial(relayCOM)
        boxes = [self.Culture1_Checkbox2_2,self.Culture2_Checkbox2_2,self.Culture3_Checkbox2_2,
                 self.Culture4_Checkbox2_2,self.Culture5_Checkbox2_2,self.Culture6_Checkbox2_2,
                 self.Culture7_Checkbox2_2,self.Culture8_Checkbox2_2]
        checkedBoxes = []
        x = 0
        for i in boxes:
            if i.isChecked():
                checkedBoxes.append(x)
            else:
                x = x + 1
        for i in checkedBoxes:
            ser.close()
            ser = serial.Serial(relayCOM)
            ser.write(("relay on " + str(i) + "\r").encode("ascii"))

#timer that updates plot 
    def update_plot_timer(self):
        timer1 = QTimer()
        timer1.timeout.connect(self.update)
        timer1.setInterval(6000)
        timer1.start()
        timers1.append(timer1)
#gives exit button functionality 
    def exitButton(self):
        sys.exit()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.Culture_Dropdown.setItemText(0, _translate("MainWindow", "Culture1"))
        self.Culture_Dropdown.setItemText(1, _translate("MainWindow", "Culture2"))
        self.Culture_Dropdown.setItemText(2, _translate("MainWindow", "Culture3"))
        self.Culture_Dropdown.setItemText(3, _translate("MainWindow", "Culture4"))
        self.Culture_Dropdown.setItemText(4, _translate("MainWindow", "Culture5"))
        self.Culture_Dropdown.setItemText(5, _translate("MainWindow", "Culture6"))
        self.Nutrient_Levels_Textbox.setText(_translate("MainWindow", "Nutrient Levels"))
        self.Exit_Button1.setText(_translate("MainWindow", "Exit"))
        self.Tabs.setTabText(self.Tabs.indexOf(self.tab), _translate("MainWindow", "Nutrient Sensor Data"))
        self.Nitrite_Levels_Textbox_2.setText(_translate("MainWindow", "Nitrite Levels"))
        self.Culture2_Checkbox2_2.setText(_translate("MainWindow", "Culture 2"))
        self.Culture4_Checkbox2_2.setText(_translate("MainWindow", "Culture 4"))
        self.Text_box1_2.setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'MS Shell Dlg 2\';\"><br /></p></body></html>"))
        self.Culture1_Checkbox2_2.setText(_translate("MainWindow", "Culture 1"))
        self.Glucose_Textbox_2.setText(_translate("MainWindow", "Glucose"))
        self.Culture6_Checkbox2_2.setText(_translate("MainWindow", "Culture 6"))
        self.Culture4_Checkbox1_2.setText(_translate("MainWindow", "Culture 4"))
        self.Culture5_Checkbox1_2.setText(_translate("MainWindow", "Culture 5"))
        self.Culture3_Checkbox1_2.setText(_translate("MainWindow", "Culture 3"))
        self.Culture6_Checkbox1_2.setText(_translate("MainWindow", "Culture 6"))
        self.Deposit_Button1_2.setText(_translate("MainWindow", "Deposit"))
        self.Culture2_Checkbox1_2.setText(_translate("MainWindow", "Culture 2"))
        self.Nitrite_Textbox_2.setText(_translate("MainWindow", "Nitrite"))
        self.Culture5_Checkbox2_2.setText(_translate("MainWindow", "Culture 5"))
        self.Culture3_Checkbox2_2.setText(_translate("MainWindow", "Culture 3"))
        self.Deposit_Button2_2.setText(_translate("MainWindow", "Deposit"))
        self.Glucose_Levels_Textbox_2.setText(_translate("MainWindow", "Glucose Levels"))
        self.Culture1_Checkbox1_2.setText(_translate("MainWindow", "Culture 1"))
        self.Exit_Button2.setText(_translate("MainWindow", "Exit"))
        self.Open_button1.setText(_translate("MainWindow", "Open All"))
        self.Close_button1.setText(_translate("MainWindow", "Close All"))
        self.Open_button2.setText(_translate("MainWindow", "Open All"))
        self.Close_button2.setText(_translate("MainWindow", "Close All"))
        self.Culture7_Checkbox1_2.setText(_translate("MainWindow", "Culture 7"))
        self.Culture8_Checkbox1_2.setText(_translate("MainWindow", "Culture 8"))
        self.Culture7_Checkbox2_2.setText(_translate("MainWindow", "Culture 7"))
        self.Culture8_Checkbox2_2.setText(_translate("MainWindow", "Culture 8"))
        self.Tabs.setTabText(self.Tabs.indexOf(self.tab_2), _translate("MainWindow", "Nutrient Depositing"))
        self.actionNew_File.setText(_translate("MainWindow", "New File"))
        self.actionOpen_File.setText(_translate("MainWindow", "Open File"))
        self.actionSave_File.setText(_translate("MainWindow", "Save File"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
from pyqtgraph import PlotWidget

#runs the GUI
def run_program():
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    app.exec_()

run_program()
