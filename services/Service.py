from email.policy import default
import os
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication,QVariant
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

debug=True
tag="QRealTime"

class Service (QTableWidget):
    def __init__(self,parent,caller):
        super(Service, self).__init__(parent)
        self.parent = parent
        self.iface=caller.iface
        self.resize(QSize(310,260))
        self.setParameters()
        self.setColumnCount(2)
        self.setColumnWidth(0, 152)
        self.setColumnWidth(1, 152)
        self.setRowCount(len(self.parameters)-1)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()

        S = QSettings()
        for row,parameter in enumerate(self.parameters):
            if row == 0:
                self.service_id = parameter[1]
                continue
            row = row -1
            pKey = QTableWidgetItem (parameter[0])
            pKey.setFlags(pKey.flags() ^ Qt.ItemIsEditable)
            pValue = QTableWidgetItem (parameter[1])
            self.setItem(row,0,pKey)
            valueFromSettings = S.value("QRealTime/%s/%s/" % (self.service_id,self.item(row,0).text()), defaultValue =  "undef")
            if not valueFromSettings or valueFromSettings == "undef":
                self.setItem(row,1,pValue)
                S.setValue("QRealTime/%s/%s/" % (self.service_id,self.item(row,0).text()),parameter[1])
            else:
                self.setItem(row,1,QTableWidgetItem (valueFromSettings))

    def getServiceName(self):
        return "Unamed"

  # Helper methods
    def print(self, text, opt=None):
        """ to redirect print to MessageLog"""
        if debug:
            QgsMessageLog.logMessage(str(text)+str(opt),tag=tag,level=Qgis.Info)

    def getProxiesConf(self):
        s = QSettings() #getting proxy from qgis options settings
        proxyEnabled = s.value("proxy/proxyEnabled", "")
        proxyType = s.value("proxy/proxyType", "" )
        proxyHost = s.value("proxy/proxyHost", "" )
        proxyPort = s.value("proxy/proxyPort", "" )
        proxyUser = s.value("proxy/proxyUser", "" )
        proxyPassword = s.value("proxy/proxyPassword", "" )
        if proxyEnabled == "true" and proxyType == 'HttpProxy': # test if there are proxy settings
            proxyDict = {
                "http"  : "http://%s:%s@%s:%s" % (proxyUser,proxyPassword,proxyHost,proxyPort),
                "https" : "http://%s:%s@%s:%s" % (proxyUser,proxyPassword,proxyHost,proxyPort)
            }
            return proxyDict
        else:
            return None

    def qtype(self, odktype):
        if odktype == 'binary':
            return QVariant.String,{'DocumentViewer': 2, 'DocumentViewerHeight': 0, 'DocumentViewerWidth': 0, 'FileWidget': True, 'FileWidgetButton': True, 'FileWidgetFilter': '', 'PropertyCollection': {'name': None, 'properties': {}, 'type': 'collection'}, 'RelativeStorage': 0, 'StorageMode': 0}
        elif odktype=='string':
            return QVariant.String,{}
        elif odktype[:3] == 'sel' :
            return QVariant.String,{}
        elif odktype[:3] == 'int':
            return QVariant.Int, {}
        elif odktype[:3]=='dat':
            return QVariant.Date, {}
        elif odktype[:3]=='ima':
            return QVariant.String,{'DocumentViewer': 2, 'DocumentViewerHeight': 0, 'DocumentViewerWidth': 0, 'FileWidget': True, 'FileWidgetButton': True, 'FileWidgetFilter': '', 'PropertyCollection': {'name': None, 'properties': {}, 'type': 'collection'}, 'RelativeStorage': 0, 'StorageMode': 0}
        elif odktype == 'Hidden':
            return 'Hidden'
        else:
            return (QVariant.String),{}

    def QVariantToODKtype(self, q_type):
        if  q_type == QVariant.String:
            return 'text'
        elif q_type == QVariant.Date:
            return 'datetime'
        elif q_type in [2,3,4,32,33,35,36]:
            return 'integer'
        elif q_type in [6,38]:
            return 'decimal'
        else:
            return 'text'

    # Service methods
    def tr(self, message):
        """Get the translation for a string using Qt translation API.
            We implement this ourselves since we do not inherit QObject.
            :param message: String for translation.
            :type message: str, QString
            :returns: Translated version of message.
            :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate(self.__class__.__name__, message)


    def guessWKTGeomType(self,geom):
        if geom:
            coordinates = geom.split(';')
        else:
            return 'error'
    #        print ('coordinates are '+ coordinates)
        firstCoordinate = coordinates[0].strip().split(" ")
        if len(firstCoordinate) < 2:
            return "invalid", None
        coordinatesList = []
        for coordinate in coordinates:
            decodeCoord = coordinate.strip().split(" ")
#            print 'decordedCoord is'+ decodeCoord
        try:
            coordinatesList.append([decodeCoord[0],decodeCoord[1]])
        except:
            pass
        if len(coordinates) == 1:

            reprojectedPoint = self.transformToLayerSRS(QgsPoint(float(coordinatesList[0][1]),float(coordinatesList[0][0])))
            return "POINT(%s %s)" % (reprojectedPoint.x(), reprojectedPoint.y()) #geopoint
        else:
            coordinateString = ""
            for coordinate in coordinatesList:
                reprojectedPoint = self.transformToLayerSRS(QgsPoint(float(coordinate[1]), float(coordinate[0])))
                coordinateString += "%s %s," % (reprojectedPoint.x(), reprojectedPoint.y())
            coordinateString = coordinateString[:-1]
        if  coordinatesList[0][0] == coordinatesList[-1][0] and coordinatesList[0][1] == coordinatesList[-1][1]:
            return "POLYGON((%s))" % coordinateString #geoshape #geotrace
        else:
            return "LINESTRING(%s)" % coordinateString


    def transformToLayerSRS(self, pPoint):
        # transformation from the current SRS to WGS84
        crsDest = self.processingLayer.crs () # get layer crs
        crsSrc = QgsCoordinateReferenceSystem("EPSG:4326")  # WGS 84
        xform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
        try:
            return QgsPoint(xform.transform(pPoint))
        except :
            return QgsPoint(xform.transform(QgsPointXY(pPoint)))

    # helper - gets list of UUID values in the layer
    def getUUIDList(self,lyr):
        uuidList = []
        uuidFieldName=None
        QgisFieldsList = [field.name() for field in lyr.fields()]
        for field in QgisFieldsList:
            if 'UUID' in field:
                uuidFieldName =field
        if uuidFieldName:
            self.print(uuidFieldName)
            for qgisFeature in lyr.getFeatures():
                uuidList.append(qgisFeature[uuidFieldName])
        self.print (uuidList)
        return uuidList

    def getServiceName(self):
        return self.service_id

    def test(self,task,a,b):
        self.print(a,b)
        return [a,b]

    def comp(self,exception,result):
        if exception:
            self.print("exception in task execution")
        response=result['response']
        remoteTable=result['table']
        lastID=result['lastID']
        if response.status_code == 200:
            self.print ('after task finished before update layer')
            if remoteTable:
                self.print ('task has returned some data')
                self.updateLayer(self.layer,remoteTable,self.geoField)
                self.print("lastID is",lastID)
                self.getValue(self.tr("last Submission"),lastID)
                self.iface.messageBar().pushSuccess(self.tag,self.tr("Data imported Successfully"))
        else:
            self.iface.messageBar().pushCritical(self.tag,self.tr("Not able to collect data"))

    def collectData(self,layer,xFormKey,doImportData=False,topElement='',version=None,geoField=''):
#        if layer :
#            self.print("layer is not present or not valid")
#            return
        def testc(exception,result):
            if exception:
                self.print("task raised exception")
            else:
                self.print("Success",result[0])
                self.print("task returned")

        self.updateFields(layer)
        self.layer=layer
        self.turl=self.getValue('url')
        self.lastID=self.getValue('last Submission')
        self.proxyConfig= self.getProxiesConf()
        self.xFormKey=xFormKey
        self.isImportData=doImportData
        self.topElement=topElement
        self.version=version
        self.print("task is being created")
        self.backgroundTask('downloading data',self.getTable, on_finished=self.comp)
        # self.task1 = QgsTask.fromFunction('downloading data',self.getTable, on_finished=self.comp)
        # self.print("task is created")
        # self.print("task status1 is  ",self.task1.status())
        # QgsApplication.taskManager().addTask(self.task1)
        # self.print("task added to taskmanager")
        # self.print("task status2 is  ",self.task1.status())
        # #task1.waitForFinished()
        # self.print("task status3 is  ",self.task1.status())
        # #response, remoteTable = self.getTable(xFormKey,importData,topElement,version)

    # helper - add ODKUUID or otherwise specified field to the layer
    def updateFields(self,layer,text='ODKUUID',q_type=QVariant.String,config={}):
        flag=True
        for field in layer.fields():

            if field.name()[:10] == text[:10]:
                flag=False
                self.print("not writing fields")
        if flag:
            uuidField = QgsField(text, q_type)
            if q_type == QVariant.String:
                uuidField.setLength(300)
            layer.dataProvider().addAttributes([uuidField])
            layer.updateFields()
        fId= layer.dataProvider().fieldNameIndex(text)
        try:
            if config['type']== 'Hidden':
                self.print('setting hidden widget')
                layer.setEditorWidgetSetup( fId, QgsEditorWidgetSetup( "Hidden" ,config ) )
                return
        except Exception as e:
            self.print(e)
        if config=={}:
            return
        self.print('now setting exernal resource widgt')
        layer.setEditorWidgetSetup( fId, QgsEditorWidgetSetup( "ExternalResource" ,config ) )

    # UI - updates visible layer given layer data
    def updateLayer(self,layer,dataDict,geoField=''):
        #print "UPDATING N.",len(dataDict),'FEATURES'
        self.processingLayer = layer
        QgisFieldsList = [field.name() for field in layer.fields()]
        #layer.beginEditCommand("ODK syncronize")
#        layer.startEditing()
        type=layer.geometryType()
        geo=['POINT','LINE','POLYGON']
        layerGeo=geo[type]

        uuidList = self.getUUIDList(self.processingLayer)

        newQgisFeatures = []
        fieldError = None
        self.print('geofield is',geoField)
        for odkFeature in dataDict:
            #print(odkFeature)
            id=None
            try:
                id= odkFeature['ODKUUID']
                self.print('odk id is',id)
            except:
                self.print('error in reading ODKUUID')
            try:
                if not id in uuidList:
                    qgisFeature = QgsFeature()
                    self.print("odkFeature",odkFeature)
                    wktGeom = self.guessWKTGeomType(odkFeature[geoField])
                    self.print (wktGeom)
                    if wktGeom[:3] != layerGeo[:3]:
                        self.print(wktGeom,'is not matching'+layerGeo)
                        continue
                    qgisGeom = QgsGeometry.fromWkt(wktGeom)
                    self.print('geom is',qgisGeom)
                    qgisFeature.setGeometry(qgisGeom)
                    qgisFeature.initAttributes(len(QgisFieldsList))
                    for fieldName, fieldValue in odkFeature.items():
                        if fieldName != geoField:
                            try:
                                qgisFeature.setAttribute(QgisFieldsList.index(fieldName[:10]),fieldValue)
                            except:
                                fieldError = fieldName
                    newQgisFeatures.append(qgisFeature)
            except Exception as e:
                    self.print('unable to create',e)
        try:
            with edit(layer):
                layer.addFeatures(newQgisFeatures)
        except:
            self.iface.messageBar().pushCritical(self.tag,"Stop layer editing and import again")
        self.processingLayer = None

    # UI - get value out of settins table
    def getValue(self,key, newValue = None):
        print("searching in setting parameter",key)
        for row in range (0,self.rowCount()):
            print(" parameter is",self.item(row,0).text())
            if self.item(row,0).text() == key:
                if newValue:
                    self.item(row, 1).setText(str(newValue))
                    print("setting new value",newValue)
                    self.setup() #store to settings
                value=self.item(row,1).text().strip()
                if value:
                    if key=='url':
                        if not value.endswith('/'):
                            value=value+'/'
                    return value

    def setup(self):
        S = QSettings()
        S.setValue("QRealTime/", self.parent.parent().currentIndex())
        for row in range (0,self.rowCount()):
            S.setValue("QRealTime/%s/%s/" % (self.service_id,self.item(row,0).text()),self.item(row,1).text())

    def backgroundTask(self, taskName, func, callback=None):
        if callback is None:
            callback = self.defaultCallback
        self.task = QgsTask.fromFunction(taskName, func, on_finished=callback)
        QgsApplication.taskManager().addTask(self.task)

    # if "task" value given in result (representing the task.description()), will specify task in message
    def defaultCallback(self, exception, result):
        if exception is None:
            taskName = ""
            if 'task' in result:
                taskName = ": " + result['task']
            if result is None:
                self.iface.messageBar().pushCritical(self.tag,self.tr("Unsuccessful Task" + taskName))
            else:
                self.iface.messageBar().pushSuccess(self.tag,self.tr("Successful Task" + taskName))
        else:
            self.print("exception in task execution")

    # Implement in subclass
    def makeOnline(self):
        raise NotImplementedError

    def importData(self):
        raise NotImplementedError

    def getFormList(self):
        raise NotImplementedError

    def setParameters(self):
        raise NotImplementedError
