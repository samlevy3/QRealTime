# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QRealTimeDialog
                                 A QGIS plugin
 This plugin connects you to Aggregate Server and do autoupdation of data to and from aggregate
                             -------------------
        begin                : 2017-08-09
        git sha              : $Format:%H$
        copyright            : (C) 2017 by IIRS
        email                : kotishiva@gmail.com
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
from PyQt5 import QtGui, uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget,QTableWidget,QTableWidgetItem
from PyQt5.QtCore import Qt, QSettings, QSize,QVariant, QTranslator, qVersion, QCoreApplication
import xml.etree.ElementTree as ET
import requests
from qgis.gui import QgsMessageBar
from qgis.core import QgsProject,QgsFeature,QgsGeometry,QgsField, QgsCoordinateReferenceSystem, QgsPoint, QgsCoordinateTransform,edit,QgsPointXY,QgsEditorWidgetSetup,QgsTaskManager,QgsTask,QgsApplication
import six
from six.moves import range
from qgis.core import QgsMessageLog, Qgis
import datetime
import site
import json
site.addsitedir(os.path.dirname(__file__))
from pyxform.builder import create_survey_element_from_dict
from .services import Service, Central, Aggregate, Kobo

debug=True
tag="QRealTime"
def print(text,opt=None):
    """ to redirect self.print to MessageLog"""
    if debug:
        QgsMessageLog.logMessage(str(text)+str(opt),tag=tag,level=Qgis.Info)
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'QRealTime_dialog_services.ui'))

class QRealTimeDialog(QtWidgets.QDialog, FORM_CLASS):
    services = [Aggregate.Aggregate, Kobo.Kobo, Central.Central]
    def __init__(self, caller,parent=None):
        """Constructor."""
        super(QRealTimeDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        i=0
        for service in self.services:
            if i>0:
                container = QWidget()
                container.resize(QSize(310,260))
                self.tabServices.addTab(container,"")
            container = self.tabServices.widget(i)
            print (container)
            service_class = service(container, caller)
            self.tabServices.setTabText(i, service_class.getServiceName())
            i=i+1

    def getCurrentService(self):
        return self.tabServices.currentWidget().children()[0]



