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
from .services.Service import Service
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
debug=True
tag="QRealTime"
def print(text,opt=None):
    """ to redirect self.print to MessageLog"""
    if debug:
        QgsMessageLog.logMessage(str(text)+str(opt),tag=tag,level=Qgis.Info)
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'QRealTime_dialog_services.ui'))

# def getProxiesConf():
#     s = QSettings() #getting proxy from qgis options settings
#     proxyEnabled = s.value("proxy/proxyEnabled", "")
#     proxyType = s.value("proxy/proxyType", "" )
#     proxyHost = s.value("proxy/proxyHost", "" )
#     proxyPort = s.value("proxy/proxyPort", "" )
#     proxyUser = s.value("proxy/proxyUser", "" )
#     proxyPassword = s.value("proxy/proxyPassword", "" )
#     if proxyEnabled == "true" and proxyType == 'HttpProxy': # test if there are proxy settings
#         proxyDict = {
#             "http"  : "http://%s:%s@%s:%s" % (proxyUser,proxyPassword,proxyHost,proxyPort),
#             "https" : "http://%s:%s@%s:%s" % (proxyUser,proxyPassword,proxyHost,proxyPort)
#         }
#         return proxyDict
#     else:
#         return None
# def qtype(odktype):
#     if odktype == 'binary':
#         return QVariant.String,{'DocumentViewer': 2, 'DocumentViewerHeight': 0, 'DocumentViewerWidth': 0, 'FileWidget': True, 'FileWidgetButton': True, 'FileWidgetFilter': '', 'PropertyCollection': {'name': None, 'properties': {}, 'type': 'collection'}, 'RelativeStorage': 0, 'StorageMode': 0}
#     elif odktype=='string':
#         return QVariant.String,{}
#     elif odktype[:3] == 'sel' :
#         return QVariant.String,{}
#     elif odktype[:3] == 'int':
#         return QVariant.Int, {}
#     elif odktype[:3]=='dat':
#         return QVariant.Date, {}
#     elif odktype[:3]=='ima':
#         return QVariant.String,{'DocumentViewer': 2, 'DocumentViewerHeight': 0, 'DocumentViewerWidth': 0, 'FileWidget': True, 'FileWidgetButton': True, 'FileWidgetFilter': '', 'PropertyCollection': {'name': None, 'properties': {}, 'type': 'collection'}, 'RelativeStorage': 0, 'StorageMode': 0}
#     elif odktype == 'Hidden':
#         return 'Hidden'
#     else:
#         return (QVariant.String),{}
# def QVariantToODKtype(q_type):
#         if  q_type == QVariant.String:
#             return 'text'
#         elif q_type == QVariant.Date:
#             return 'datetime'
#         elif q_type in [2,3,4,32,33,35,36]:
#             return 'integer'
#         elif q_type in [6,38]:
#             return 'decimal'
#         else:
#             return 'text'
class QRealTimeDialog(QtWidgets.QDialog, FORM_CLASS):
    services = ['Aggregate','Kobo', 'Central']
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
            serviceClass = globals()[service]
            serviceClass(container,caller)
            self.tabServices.setTabText(i, service)
            i=i+1

    def getCurrentService(self):
        return self.tabServices.currentWidget().children()[0]

class Aggregate (Service):
    # def tr(self, message):
    #     """Get the translation for a string using Qt translation API.
    #         We implement this ourselves since we do not inherit QObject.
    #         :param message: String for translation.
    #         :type message: str, QString
    #         :returns: Translated version of message.
    #         :rtype: QString
    #     """
    #     # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
    #     return QCoreApplication.translate(self.__class__.__name__, message)
    tag='ODK Aggregate'
    def __init__(self,parent,caller):
        super(Aggregate, self).__init__(parent, caller)
        # self.parent = parent
        # self.iface=caller.iface
        # self.resize(QSize(310,260))
        # self.setParameters()
        # self.setColumnCount(2)
        # self.setColumnWidth(0, 152)
        # self.setColumnWidth(1, 152)
        # self.setRowCount(len(self.parameters)-1)
        # self.verticalHeader().hide()
        # self.horizontalHeader().hide()
        self.tag='ODK Aggregate'

        # S = QSettings()
        # for row,parameter in enumerate(self.parameters):
        #     if row == 0:
        #         self.service_id = parameter[1]
        #         continue
        #     row = row -1
        #     pKey = QTableWidgetItem (parameter[0])
        #     pKey.setFlags(pKey.flags() ^ Qt.ItemIsEditable)
        #     pValue = QTableWidgetItem (parameter[1])
        #     self.setItem(row,0,pKey)
        #     valueFromSettings = S.value("QRealTime/%s/%s/" % (self.service_id,self.item(row,0).text()), defaultValue =  "undef")
        #     if not valueFromSettings or valueFromSettings == "undef":
        #         self.setItem(row,1,pValue)
        #         S.setValue("QRealTime/%s/%s/" % (self.service_id,self.item(row,0).text()),parameter[1])
        #     else:
        #         self.setItem(row,1,QTableWidgetItem (valueFromSettings))
    def setParameters(self):
        self.parameters =[
        ["id","Aggregate"],
        ["url",''],
        [self.tr("user"), ''],
        [self.tr("password"), ''],
        [self.tr("last Submission"),''],
        [self.tr('sync time'),3600]
        ]
    # def getServiceName(self):
    #     return self.service_id

    def getAuth(self):
        auth = requests.auth.HTTPDigestAuth(self.getValue(self.tr('user')),self.getValue(self.tr('password')))
        return auth

    # def setup(self):
    #     S = QSettings()
    #     S.setValue("QRealTime/", self.parent.parent().currentIndex())
    #     for row in range (0,self.rowCount()):
    #         S.setValue("QRealTime/%s/%s/" % (self.service_id,self.item(row,0).text()),self.item(row,1).text())

    # def getValue(self,key, newValue = None):
    #     self.print("searching in setting parameter",key)
    #     for row in range (0,self.rowCount()):
    #         self.print(" parameter is",self.item(row,0).text())
    #         if self.item(row,0).text() == key:
    #             if newValue:
    #                 self.item(row, 1).setText(str(newValue))
    #                 self.print("setting new value",newValue)
    #                 self.setup() #store to settings
    #             value=self.item(row,1).text().strip()
    #             if value:
    #                 if key=='url':
    #                     if not value.endswith('/'):
    #                         value=value+'/'
    #                 return value

#     def guessWKTGeomType(self,geom):
#         if geom:
#             coordinates = geom.split(';')
#         else:
#             return 'error'
# #        self.print ('coordinates are '+ coordinates)
#         firstCoordinate = coordinates[0].strip().split(" ")
#         if len(firstCoordinate) < 2:
#             return "invalid", None
#         coordinatesList = []
#         for coordinate in coordinates:
#             decodeCoord = coordinate.strip().split(" ")
# #            self.print 'decordedCoord is'+ decodeCoord
#             try:
#                 coordinatesList.append([decodeCoord[0],decodeCoord[1]])
#             except:
#                 pass
#         if len(coordinates) == 1:

#             reprojectedPoint = self.transformToLayerSRS(QgsPoint(float(coordinatesList[0][1]),float(coordinatesList[0][0])))
#             return "POINT(%s %s)" % (reprojectedPoint.x(), reprojectedPoint.y()) #geopoint
#         else:
#             coordinateString = ""
#             for coordinate in coordinatesList:
#                 reprojectedPoint = self.transformToLayerSRS(QgsPoint(float(coordinate[1]), float(coordinate[0])))
#                 coordinateString += "%s %s," % (reprojectedPoint.x(), reprojectedPoint.y())
#             coordinateString = coordinateString[:-1]
#         if  coordinatesList[0][0] == coordinatesList[-1][0] and coordinatesList[0][1] == coordinatesList[-1][1]:
#             return "POLYGON((%s))" % coordinateString #geoshape #geotrace
#         else:
#             return "LINESTRING(%s)" % coordinateString


#    def getExportExtension(self):
#        return 'xml'

    def getFormList(self):
        method='GET'
        url=self.getValue('url')
        if url:
            furl=url+'//formList'
        else:
            self.iface.messageBar().pushWarning(self.tag,self.tr("Enter url in settings"))
            return None,None
        try:
            response= requests.request(method,furl,proxies=self.getProxiesConf(),auth=self.getAuth(),verify=False)
        except:
            self.iface.messageBar().pushWarning(self.tag,self.tr("Not able to connect to server"))
            return None,None
        if response:
            try:
                root=ET.fromstring(response.content)
                keylist=[form.attrib['url'].split('=')[1] for form in root.findall('form')]
                forms= {key:key for key in keylist}
                return forms,response
            except:
                self.iface.messageBar().pushWarning(self.tag,self.tr("Not able to parse form list"))
        return None,None
    def importData(self,layer,selectedForm,importData):
        url=self.getValue('url')
        if url:
            furl=url+'//formXml?formId='+selectedForm
        else:
            self.iface.messageBar().pushWarning(self.tag,self.tr("Enter url in settings"))
            return
        try:
            response= requests.request('GET',furl,proxies=self.getProxiesConf(),auth=self.getAuth(),verify=False)
        except:
            self.iface.messageBar().pushWarning(self.tag,self.tr("Not able to connect to server"))
            return
        if response.status_code==200:
            # with open('importForm.xml','w') as importForm:
            #     importForm.write(response.content)
            self.formKey,self.topElement,self.version,self.geoField = self.updateLayerXML(layer,response.content)
            layer.setName(self.formKey)
            self.print("calling collect data")
            self.collectData(layer,self.formKey,importData,self.topElement,self.version,self.geoField)
        else:
            self.iface.messageBar().pushWarning(self.tag,self.tr("Not able to collect data from server"))
    def getFieldsModel(self,currentLayer):
        fieldsModel = []
        g_type= currentLayer.geometryType()
        fieldDef={'name':'GEOMETRY','type':'geopoint','bind':{'required':'true()'}}
        fieldDef['Appearance']= 'maps'
        if g_type==0:
            fieldDef['label']='add point location'
        elif g_type==1:
            fieldDef['label']='Draw Line'
            fieldDef['type']='geotrace'
        else:
            fieldDef['label']='Draw Area'
            fieldDef['type']='geoshape'
        fieldsModel.append(fieldDef)
        i=0
        for field in currentLayer.fields():
            widget =currentLayer.editorWidgetSetup(i)
            fwidget = widget.type()
            if (fwidget=='Hidden'):
                i+=1
                continue

            fieldDef = {}
            fieldDef['name'] = field.name()
            fieldDef['map'] = field.name()
            fieldDef['label'] = field.alias() or field.name()
            fieldDef['hint'] = ''
            fieldDef['type'] = self.QVariantToODKtype(field.type())
            fieldDef['bind'] = {}
#            fieldDef['fieldWidget'] = currentFormConfig.widgetType(i)
            fieldDef['fieldWidget']=widget.type()
            self.print('getFieldModel',fieldDef['fieldWidget'])
            if fieldDef['fieldWidget'] in ('ValueMap','CheckBox','Photo','ExternalResource'):
                if fieldDef['fieldWidget'] == 'ValueMap':
                    fieldDef['type']='select one'
                    valueMap=widget.config()['map']
                    config={}
                    for value in valueMap:
                        for k,v in value.items():
                                config[v]=k
                    self.print('configuration is ',config)
                    choicesList=[{'name':name,'label':label} for name,label in config.items()]
                    fieldDef["choices"] = choicesList
                elif fieldDef['fieldWidget'] == 'Photo' or fieldDef['fieldWidget'] == 'ExternalResource' :
                    fieldDef['type']='image'
                    self.print('got an image type field')

#                fieldDef['choices'] = config
            else:
                fieldDef['choices'] = {}
            if fieldDef['name'] == 'ODKUUID':
                fieldDef["bind"] = {"readonly": "true()", "calculate": "concat('uuid:', uuid())"}
            if fieldDef['fieldWidget'] == 'DateTime':
                fieldDef["type"] = 'date'
            fieldsModel.append(fieldDef)
            i+=1
        return fieldsModel
    def updateLayerXML(self,layer,xml):
        ns='{http://www.w3.org/2002/xforms}'
        root= ET.fromstring(xml)
        #key= root[0][1][0][0].attrib['id']
        instance=root[0][1].find(ns+'instance')
        key=instance[0].attrib['id']
        #topElement=root[0][1][0][0].tag.split('}')[1]
        topElement=instance[0].tag.split('}')[1]
        try:
            version=instance[0].attrib['version']
        except:
            version='null'
        self.print('key captured'+ key)
        self.print (root[0][1].findall(ns+'bind'))
        for bind in root[0][1].findall(ns+'bind'):
            attrib=bind.attrib
            self.print (attrib)
            fieldName= attrib['nodeset'].split('/')[-1]
            try:
                fieldType=attrib['type']
            except:
                continue
            #self.print('attrib type is',attrib['type'])
            qgstype,config = self.qtype(attrib['type'])
            #self.print ('first attribute'+ fieldName)
            inputs=root[1].findall('.//*[@ref]')
            if fieldType[:3]!='geo':
                self.print('creating new field:'+ fieldName)
                isHidden= True
                for input in inputs:
                    if fieldName == input.attrib['ref'].split('/')[-1]:
                        isHidden= False
                        break
                if isHidden:
                    #self.print('Reached Hidden')
                    config['type']='Hidden'
                self.updateFields(layer,fieldName,qgstype,config)
            else:
                geoField=fieldName
        return key,topElement,version,geoField
    def prepareSendForm(self,layer):
        self.updateFields(layer)
        version= str(datetime.date.today())
        fieldDict= self.getFieldsModel(layer)
        self.print ('fieldDict',fieldDict)
        surveyDict= {"name":layer.name(),"title":layer.name(),'VERSION':version,"instance_name": 'uuid()',"submission_url": '',
        "default_language":'default','id_string':layer.name(),'type':'survey','children':fieldDict }
        survey=create_survey_element_from_dict(surveyDict)
        try:
            xml=survey.to_xml(validate=None, warnings='warnings')
            os.chdir(os.path.expanduser('~'))
            self.sendForm(layer.name(),xml)
        except Exception as e:
            self.print("error in creating xform xml",e)
            self.iface.messageBar().pushCritical(self.tag,self.tr("Survey form can't be created, check layer name"))
    def sendForm(self,xForm_id,xml):
#        step1 - verify if form exists:
        formList, response = self.getFormList()
        if not response:
           self.iface.messageBar().pushCritical(self.tag,self.tr("Can not connect to server"))
           return response
        form_key = xForm_id in formList
        message =''
        if form_key:
            message= 'Form Updated'
            method = 'POST'
            url = self.getValue('url')+'//formUpload'
        else:
            message= 'Created new form'
            method = 'POST'
            url = self.getValue('url')+'//formUpload'
#        method = 'POST'
#        url = self.getValue('url')+'//formUpload'
        #step2 - upload form
        with open('xForm.xml','w')as xForm:
            xForm.write(xml)
        file = open('xForm.xml','r')
        files = {'form_def_file':file}
        response = requests.request(method, url,files = files, proxies = self.getProxiesConf(),auth=self.getAuth(),verify=False )
        if response.status_code== 201:
            self.iface.messageBar().pushSuccess(self.tag,
                                                self.tr('Layer is online('+message+'), Collect data from App'))
        elif response.status_code == 409:
            self.iface.messageBar().pushWarning(self.tag,self.tr("Form exists and can not be updated"))
        else:
            self.iface.messageBar().pushCritical(self.tag,self.tr("Form is not sent"))
        file.close()
        return response
    # def test(self,task,a,b):
    #     self.print(a,b)
    #     return [a,b]
    # def comp(self,exception,result):
    #     if exception:
    #         self.print("exception in task execution")
    #     response=result['response']
    #     remoteTable=result['table']
    #     lastID=result['lastID']
    #     if response.status_code == 200:
    #         self.print ('after task finished before update layer')
    #         if remoteTable:
    #             self.print ('task has returned some data')
    #             self.updateLayer(self.layer,remoteTable,self.geoField)
    #             self.print("lastID is",lastID)
    #             self.getValue(self.tr("last Submission"),lastID)
    #             self.iface.messageBar().pushSuccess(self.tag,self.tr("Data imported Successfully"))
    #     else:
    #         self.iface.messageBar().pushCritical(self.tag,self.tr("Not able to collect data"))

#     def collectData(self,layer,xFormKey,doImportData=False,topElement='',version=None,geoField=''):
# #        if layer :
# #            self.print("layer is not present or not valid")
# #            return
#         def testc(exception,result):
#             if exception:
#                 self.print("task raised exception")
#             else:
#                 self.print("Success",result[0])
#                 self.print("task returned")

#         self.updateFields(layer)
#         self.layer=layer
#         self.turl=self.getValue('url')
#         self.lastID=self.getValue('last Submission')
#         self.proxyConfig= self.getProxiesConf()
#         self.xFormKey=xFormKey
#         self.isImportData=doImportData
#         self.topElement=topElement
#         self.version=version
#         self.print("task is being created")
#         self.task1 = QgsTask.fromFunction('downloading data',self.getTable, on_finished=self.comp)
#         self.print("task is created")
#         self.print("task status1 is  ",self.task1.status())
#         QgsApplication.taskManager().addTask(self.task1)
#         self.print("task added to taskmanager")
#         self.print("task status2 is  ",self.task1.status())
#         #task1.waitForFinished()
#         self.print("task status3 is  ",self.task1.status())
#         #response, remoteTable = self.getTable(xFormKey,importData,topElement,version)


    # def updateFields(self,layer,text='ODKUUID',q_type=QVariant.String,config={}):
    #     flag=True
    #     for field in layer.fields():

    #         if field.name()[:10] == text[:10]:
    #             flag=False
    #             self.print("not writing fields")
    #     if flag:
    #         uuidField = QgsField(text, q_type)
    #         if q_type == QVariant.String:
    #             uuidField.setLength(300)
    #         layer.dataProvider().addAttributes([uuidField])
    #         layer.updateFields()
    #     fId= layer.dataProvider().fieldNameIndex(text)
    #     try:
    #         if config['type']== 'Hidden':
    #             self.print('setting hidden widget')
    #             layer.setEditorWidgetSetup( fId, QgsEditorWidgetSetup( "Hidden" ,config ) )
    #             return
    #     except Exception as e:
    #         self.print(e)
    #     if config=={}:
    #         return
    #     self.print('now setting exernal resource widgt')
    #     layer.setEditorWidgetSetup( fId, QgsEditorWidgetSetup( "ExternalResource" ,config ) )
#     def updateLayer(self,layer,dataDict,geoField=''):
#         #self.print "UPDATING N.",len(dataDict),'FEATURES'
#         self.processingLayer = layer
#         QgisFieldsList = [field.name() for field in layer.fields()]
#         #layer.beginEditCommand("ODK syncronize")
# #        layer.startEditing()
#         type=layer.geometryType()
#         geo=['POINT','LINE','POLYGON']
#         layerGeo=geo[type]

#         uuidList = self.getUUIDList(self.processingLayer)

#         newQgisFeatures = []
#         fieldError = None
#         self.print('geofield is',geoField)
#         for odkFeature in dataDict:
#             #self.print(odkFeature)
#             id=None
#             try:
#                 id= odkFeature['ODKUUID']
#                 self.print('odk id is',id)
#             except:
#                 self.print('error in reading ODKUUID')
#             try:
#                 if not id in uuidList:
#                     qgisFeature = QgsFeature()
#                     self.print("odkFeature",odkFeature)
#                     wktGeom = self.guessWKTGeomType(odkFeature[geoField])
#                     self.print (wktGeom)
#                     if wktGeom[:3] != layerGeo[:3]:
#                         self.print(wktGeom,'is not matching'+layerGeo)
#                         continue
#                     qgisGeom = QgsGeometry.fromWkt(wktGeom)
#                     self.print('geom is',qgisGeom)
#                     qgisFeature.setGeometry(qgisGeom)
#                     qgisFeature.initAttributes(len(QgisFieldsList))
#                     for fieldName, fieldValue in odkFeature.items():
#                         if fieldName != geoField:
#                             try:
#                                 qgisFeature.setAttribute(QgisFieldsList.index(fieldName[:10]),fieldValue)
#                             except:
#                                 fieldError = fieldName

#                     newQgisFeatures.append(qgisFeature)
#             except Exception as e:
#                     self.print('unable to create',e)
#         try:
#             with edit(layer):
#                 layer.addFeatures(newQgisFeatures)
#         except:
#             self.iface.messageBar().pushCritical(self.tag,"Stop layer editing and import again")
#         self.processingLayer = None

    # def getUUIDList(self,lyr):
    #     uuidList = []
    #     uuidFieldName=None
    #     QgisFieldsList = [field.name() for field in lyr.fields()]
    #     for field in QgisFieldsList:
    #         if 'UUID' in field:
    #             uuidFieldName =field
    #     if uuidFieldName:
    #         self.print(uuidFieldName)
    #         for qgisFeature in lyr.getFeatures():
    #             uuidList.append(qgisFeature[uuidFieldName])
    #     self.print (uuidList)
    #     return uuidList

    # def transformToLayerSRS(self, pPoint):
    #     # transformation from the current SRS to WGS84
    #     crsDest = self.processingLayer.crs () # get layer crs
    #     crsSrc = QgsCoordinateReferenceSystem("EPSG:4326")  # WGS 84
    #     xform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
    #     try:
    #         return QgsPoint(xform.transform(pPoint))
    #     except :
    #         return QgsPoint(xform.transform(QgsPointXY(pPoint)))


    def getTable(self,task):
        #turl=self.getValue('url')
        self.print("calling getTable in ODK Aggregate")
        table=[]
        if self.turl:
            url=self.turl+'/view/submissionList?formId='+self.xFormKey
        else:
            self.iface.messageBar().pushWarning(self.tag,self.tr("Enter url in settings"))
            return {'response':None, 'table':table}
        method='GET'
        lastID=""
        response=None
        if not self.isImportData:
            lastID=self.lastID
        try:
            response = requests.request(method,url,proxies=self.proxyConfig,auth=self.getAuth(),verify=False)
        except:
            #self.iface.messageBar().pushCritical(self.tag,self.tr("Not able to connect to server"))
            return {'response':response, 'table':table}
        if not response.status_code == 200:
            return {'response':response, 'table':table}
        try:
            root = ET.fromstring(response.content)
            ns='{http://opendatakit.org/submissions}'
            instance_ids=[child.text for child in root[0].findall(ns+'id')]
            no_sub= len(instance_ids)
#            self.print('instance ids before filter',instance_ids)
            #self.print('number of submissions are',no_sub)
            ns1='{http://www.opendatakit.org/cursor}'
            lastReturnedURI= ET.fromstring(root[1].text).findall(ns1+'uriLastReturnedValue')[0].text
            self.print("last id  is",lastID)
            self.print( "last returned id is",lastReturnedURI)
            #self.print('server lastID is', lastReturnedURI)
            if lastID ==lastReturnedURI:
                self.print ('No Download returning')
                return {'response':response, 'table':table,'lastID':None}
            lastindex=0
            try:
                lastindex= instance_ids.index(lastID)
            except:
                self.print ('first Download')
            instance_ids=instance_ids[lastindex:]
            self.print('downloading')
            for id in instance_ids :
                if id:
                    url=self.turl+'/view/downloadSubmission'
                    #self.print (url)
                    para={'formId':'{}[@version={} and @uiVersion=null]/{}[@key={}]'.format(self.xFormKey,self.version,self.topElement,id)}
                    response=requests.request(method,url,params=para,proxies= self.proxyConfig,auth=self.getAuth(),verify=False)
                    if not response.status_code == 200:
                        return response,table
                    #self.print('xml downloaded is',response.content)
                    root1=ET.fromstring(response.content)
                    #self.print('downloaded data is',root1)
                    data=root1[0].findall(ns+self.topElement)
                    #self.print('data is',data[0])
                    dict={child.tag.split('}')[-1]:child.text for child in data[0]}
                    dict['ODKUUID']=id
                    #self.print('dictionary is',dict)
                    dict2= dict.copy()
                    for key,value in dict2.items():
                                if value is None:
                                    grEle=data[0].findall(ns+key)
                                    try:
                                        for child in grEle[0]:
                                            dict[child.tag.split('}')[-1]]=child.text
                                            #self.print('found a group element')
                                    except:
                                        #self.print('error')
                                        pass
                    mediaFiles=root1.findall(ns+'mediaFile')
                    if len(mediaFiles)>0:
                        for mediaFile in mediaFiles:
                            mediaDict={child.tag.replace(ns,''):child.text for child in mediaFile}
                            for key,value in six.iteritems(dict):
                                #self.print('value is',value)
                                if value==mediaDict['filename']:
                                    murl= mediaDict['downloadUrl']
                                    #self.print('Download url is',murl)
                                    if murl.endswith('as_attachment=true'):
                                        murl=murl[:-19]
                                        dict[key]= murl
                    table.append(dict)
            #self.getValue('lastID',lastReturnedURI)
            #self.print ('table is:',table)
            self.lastID=lastReturnedURI
            return {'response':response, 'table':table,'lastID':lastReturnedURI}
        except Exception as e:
            self.print ('not able to fetch',e)
            return {'response':response, 'table':table,'lastID':None}


class Kobo (Service):
    def __init__(self,parent,caller):
        super(Kobo, self).__init__(parent,caller)
        self.tag='Kobo'
    def setParameters(self):
        self.parameters =[
        ["id","Kobo"],
        ["url",'https://kobo.humanitarianresponse.info/'],
        [self.tr("user"), ''],
        [self.tr("password"), ''],
        [self.tr("last Submission"),''],
        [self.tr('sync time'),'']
        ]
    def prepareSendForm(self,layer):
        self.updateFields(layer)
        fieldDict,choicesList= self.getFieldsModel(layer)
        self.print ('fieldDict',fieldDict)
        payload={"uid":layer.name(),"name":layer.name(),"asset_type":"survey","content":json.dumps({"survey":fieldDict,"choices":choicesList})}
        self.print("Payload= ",payload)
        self.sendForm(layer.name(),payload)
    def sendForm(self,xForm_id,payload):
#        step1 - verify if form exists:
        formList, response = self.getFormList()
        form=''
        if not response:
            self.iface.messageBar().pushCritical(self.tag,self.tr(str('can not connect to server')))
            return response
        if xForm_id in formList:
            form=xForm_id
            xForm_id=formList[xForm_id]
        message =''
        if form:
            message= 'Form Updated'
            method = 'PATCH'
            url = self.getValue('url')+'/assets/'+xForm_id
        else:
            message= 'Created new form'
            method = 'POST'
            url = self.getValue('url')+'/assets/'
        user=self.getValue(self.tr("user"))
        password=self.getValue(self.tr("password"))
        para = {"format":"json"}
        headers = {'Content-Type': "application/json",'Accept': "application/json"}
        #creates form:
        response = requests.request(method,url,json=payload,auth=(user,password),headers=headers,params=para)
        responseJson=json.loads(response.text)
        urlDeploy = self.getValue('url')+"assets/"+responseJson['uid']+"/deployment/"
        payload2 = json.dumps({"active": True})
        #deploys form:
        response2 = requests.post(urlDeploy,data=payload2, auth=(user,password), headers=headers, params=para)
##        urlShare = self.getValue('url')+"permissions/"
##        permissions={"content_object":self.getValue('url')+"/assets/"+responseJson['uid']+"/","permission": "view_submissions","deny": False,"inherited": False,"user": "https://kobo.humanitarianresponse.info/users/AnonymousUser/"}
        urlShare = self.getValue('url')+"api/v2/assets/"+responseJson['uid']+"/permission-assignments/"
        permissions={"user":self.getValue('url')+"api/v2/users/AnonymousUser/","permission":self.getValue('url')+"api/v2/permissions/view_submissions/"}
        #shares submissions publicly:
        response3 = requests.post(urlShare, json=permissions, auth=(user,password),headers=headers)
        self.print(self.tag,response3.text)
        if response.status_code== 201 or response.status_code == 200:
            self.iface.messageBar().pushSuccess(self.tag,
                                                self.tr('Layer is online('+message+'), Collect data from App'))
        elif response.status_code == 409:
            self.iface.messageBar().pushWarning(self.tag,self.tr("Form exists and can not be updated"))
        else:
            self.iface.messageBar().pushCritical(self.tag,self.tr(str(response.status_code)))
        if not response3:
            self.iface.messageBar().pushWarning(self.tag,self.tr('Submissions not shared publicly'))
        return response
    def getFormList(self):
        user=self.getValue(self.tr("user"))
        password=self.getValue(self.tr("password"))
        turl=self.getValue('url')
        if turl:
            url=turl+'/assets/'
        else:
            self.iface.messageBar().pushWarning(self.tag,self.tr("Enter url in settings"))
            return None,None
#        self.print (url)
        para={'format':'json'}
        keyDict={}
        questions=[]
        try:
            response= requests.get(url,proxies=self.getProxiesConf(),auth=(user,password),params=para)
            forms= response.json()
            for form in forms['results']:
                if form['asset_type']=='survey' and form['deployment__active']==True:
                    keyDict[form['name']]=form['uid']
#            self.print('keyDict is',keyDict)
            return keyDict,response
        except:
            self.iface.messageBar().pushCritical(self.tag,self.tr("Invalid url username or password"))
            return None,None
    def importData(self,layer,selectedForm,doImportData=True):
        #from kobo branchQH
        user=self.getValue(self.tr("user"))
        password=self.getValue(self.tr("password"))
        turl=self.getValue('url')
        if turl:
            url=turl+'/assets/'+selectedForm
        else:
            self.iface.messageBar().pushWarning(self.tag,self.tr("Enter url in settings"))
        para={'format':'xml'}
        requests.packages.urllib3.disable_warnings()
        try:
            response= requests.request('GET',url,proxies=self.getProxiesConf(),auth=(user,password),verify=False,params=para)
        except:
            self.iface.messageBar().pushCritical(self.tag,self.tr("Invalid url,username or password"))
            return
        if response.status_code==200:
            xml=response.content
            #self.iface.messageBar().pushCritical(self.tag,self.tr(str(xml)))
            # with open('importForm.xml','w') as importForm:
            #     importForm.write(response.content)
            self.layer_name,self.version, self.geoField,self.fields= self.updateLayerXML(layer,xml)
            layer.setName(self.layer_name)
            self.user=user
            self.password=password
            self.print("calling collect data",self.tag)
            self.collectData(layer,selectedForm,doImportData,self.layer_name,self.version,self.geoField)
        else:
            self.iface.messageBar().pushWarning(self.tag,self.tr("not able to connect to server"))

    def updateLayerXML(self,layer,xml):
        geoField=''
        ns='{http://www.w3.org/2002/xforms}'
        nsh='{http://www.w3.org/1999/xhtml}'
        root= ET.fromstring(xml)
        #key= root[0][1][0][0].attrib['id']
        layer_name=root[0].find(nsh+'title').text
        instance=root[0][1].find(ns+'instance')
        fields={}
        #topElement=root[0][1][0][0].tag.split('}')[1]
        try:
            version=instance[0].attrib['version']
        except:
            version='null'
#        self.print('form name is '+ layer_name)
#        self.print (root[0][1].findall(ns+'bind'))
        for bind in root[0][1].findall(ns+'bind'):
            attrib=bind.attrib
            self.print (attrib)
            fieldName= attrib['nodeset'].split('/')[-1]
            try:
                fieldType=attrib['type']
            except:
                continue
            fields[fieldName]=fieldType
#            self.print('attrib type is',attrib['type'])
            qgstype,config = self.qtype(attrib['type'])
#            self.print ('first attribute'+ fieldName)
            inputs=root[1].findall('.//*[@ref]')
            if fieldType[:3]!='geo':
                #self.print('creating new field:'+ fieldName)
                isHidden= True
                if fieldName=='instanceID':
                    fieldName='ODKUUID'
                    fields[fieldName]=fieldType
                    isHidden= False
                for input in inputs:
                    if fieldName == input.attrib['ref'].split('/')[-1]:
                        isHidden= False
                        break
                if isHidden:
                    self.print('Reached Hidden')
                    config['type']='Hidden'
            else:
                geoField=fieldName
                self.print('geometry field is =',fieldName)
                continue
            self.updateFields(layer,fieldName,qgstype,config)
        return layer_name,version,geoField,fields

    def getTable(self,task):
        try:
            self.print("get table started",self.tag)
            #task.setProgress(10.0)
            #requests.packages.urllib3.disable_warnings()
            url=self.turl
            #task.setProgress(30.0)
            lastSub=""
            if not self.isImportData:
                lastSub=self.lastID
            urlData=url+'/api/v2/assets/'+self.xFormKey+'/data/'
            self.print('urldata is '+urlData)
            table=[]
            response=None
            if not lastSub:
                para={'format':'json'}
                try:
                    response = requests.get(urlData,proxies=self.proxyConfig,auth=(self.user,self.password),params=para,verify=False)
                except:
                    self.print("not able to connect to server",urlData)
                    return {'response':response, 'table':table}
                self.print('requesting url is'+response.url)
            else:
                query_param={"_id": {"$gt":int(lastSub)}}
                jsonquery=json.dumps(query_param)
                self.print('query_param is'+jsonquery)
                para={'query':jsonquery,'format':'json'}
                try:
                    response = requests.get(urlData,proxies=self.proxyConfig,auth=(self.user,self.password),params=para,verify=False)
                    self.print('requesting url is'+response.url)
                except:
                    self.print("not able to connect to server",urlData)
                    return {'response':response, 'table':table,'lastID':None}
            #task.setProgress(50)
            data=response.json()
            #self.print(data,type(data))
            subList=[]
            self.print("no of submissions are",data['count'])
            if data['count']==0:
                return {'response':response, 'table':table}
            for submission in data['results']:
                submission['ODKUUID']=submission['meta/instanceID']
                subID=submission['_id']
                binar_url=""
                for attachment in submission['_attachments']:
                    binar_url=attachment['download_url']
                #subTime_datetime=datetime.datetime.strptime(subTime,'%Y-%m-%dT%H:%M:%S')
                subList.append(subID)
                for key in list(submission):
                    self.print(key)
                    if key == self.geoField:
                        self.print (self.geoField)
                        continue
                    if key not in self.fields:
                        submission.pop(key)
                    else:
                        if self.fields[key]=="binary":
                            submission[key]=binar_url
                table.append(submission)
            #task.setProgress(90)
            if len(subList)>0:
                lastSubmission=max(subList)
            return {'response':response, 'table':table,'lastID':lastSubmission}
        except Exception as e:
            self.print("exception occured in gettable",e)
            return {'response':None, 'table':None,'lastID':None}

    def getFieldsModel(self,currentLayer):
        fieldsModel = []
        choicesList = []
        g_type= currentLayer.geometryType()
        fieldDef={"type":"geopoint","required":True}
#        fieldDef['Appearance']= 'maps'
        if g_type==0:
            fieldDef["label"]="Point Location"
        elif g_type==1:
            fieldDef["label"]="Draw Line"
            fieldDef["type"]="geotrace"
        else:
            fieldDef["label"]="Draw Area"
            fieldDef["type"]="geoshape"
        fieldsModel.append(fieldDef)
        i=0
        j=0
        for field in currentLayer.fields():
            if field.name()=='ODKUUID':
                i+=1
                continue
            widget =currentLayer.editorWidgetSetup(i)
            fwidget = widget.type()
            if (fwidget=='Hidden'):
                i+=1
                continue

            fieldDef = {}
            fieldDef["name"]=field.name()
            fieldDef["label"] = field.alias() or field.name()
#            fieldDef['hint'] = ''
            fieldDef["type"] = self.QVariantToODKtype(field.type())
#            fieldDef['bind'] = {}
#            fieldDef['fieldWidget'] = currentFormConfig.widgetType(i)
            fieldDef["fieldWidget"]=widget.type()
            self.print("getFieldModel",fieldDef["fieldWidget"])
            if fieldDef["fieldWidget"] in ("ValueMap","CheckBox","Photo","ExternalResource"):
                if fieldDef["fieldWidget"] == "ValueMap":
                    fieldDef["type"]="select_one"
                    j+=1
                    listName="select"+str(j)
                    fieldDef["select_from_list_name"]=listName
                    valueMap=widget.config()["map"]
                    config={}
                    for value in valueMap:
                        for k,v in value.items():
                                config[v]=k
                    self.print('configuration is ',config)
                    for name,label in config.items():
                        choicesList.append({"name":name,"label":label,"list_name":listName})
#                    fieldDef["choices"] = choicesList
                elif fieldDef["fieldWidget"] == 'Photo' or fieldDef["fieldWidget"] == 'ExternalResource' :
                    fieldDef["type"]="image"
                    self.print('got an image type field')

#                fieldDef['choices'] = config
#            else:
#                fieldDef['choices'] = {}
#            if fieldDef['name'] == 'ODKUUID':
#                fieldDef["bind"] = {"readonly": "true()", "calculate": "concat('uuid:', uuid())"}
            fieldDef.pop("fieldWidget")
            fieldsModel.append(fieldDef)
            i+=1
        return fieldsModel,choicesList

class Central (Service):

    def __init__(self,parent,caller):
        super(Central, self).__init__(parent,caller)
        # user auth token
        self.usertoken = ""
        # corresponding id for entered project name
        self.project_id = 0
        # name of selected form
        self.form_name = ""
        self.tag = "ODK Central"

    def setParameters(self):
        self.parameters =[
        ["id","Central"],
        ["url",'https://sandbox.getodk.cloud'],
        [self.tr("user"), ''],
        [self.tr("password"), ''],
        [self.tr("last Submission"),''],
        [self.tr('sync time'),''],
        [self.tr('project name'),'']
        ]

    def getFormList(self):
        """Retrieves list of all forms using user entered credentials

        Returns
        ------
        forms - dictionary
            contains all forms in user's account
        x - HTTP response
            authentication response
        """

        user=self.getValue(self.tr("user"))
        password=self.getValue(self.tr("password"))
        c_url=self.getValue('url')
        data = {'email': user, 'password' : password}
        if not c_url:
            self.iface.messageBar().pushWarning(self.tag,self.tr("Enter url in settings"))
            return None,None
        headers = {"Content-Type": "application/json"}
        projects = {}
        forms = {}
        project_name =self.getValue(self.tr("project name"))
        try:
            x  = requests.post(c_url + "v1/sessions", json = data, headers = headers)
            token = x.json()["token"]
            Central.usertoken = token
            projects_response = requests.get(c_url + "v1/projects/", headers={"Authorization": "Bearer " + token})
            for p in projects_response.json():
                if p["name"] == project_name:
                    Central.project_id = p["id"]
            form_response = requests.get(c_url + "v1/projects/"+ str(Central.project_id)+"/forms/", headers={"Authorization": "Bearer " + token})
            for form in form_response.json():
                forms[form["name"]] = form["enketoOnceId"]
            return forms, x
        except:
            self.iface.messageBar().pushCritical(self.tag,self.tr("Invalid url, username, project name or password"))
            return None,None

    def importData(self,layer,selectedForm,doImportData=True):
        """Imports user selected form from server """

        #from central
        user=self.getValue(self.tr("user"))
        project_id = Central.project_id
        password=self.getValue(self.tr("password"))
        c_url=self.getValue('url')
        if not c_url:
            self.iface.messageBar().pushWarning(self.tag,self.tr("Enter url in settings"))
            return None,None
        data = {'email': user, 'password' : password}
        headers = {"Content-Type": "application/json"}
        requests.packages.urllib3.disable_warnings()
        selectedFormName = ""
        form_response = requests.get(c_url + "v1/projects/"+ str(project_id)+"/forms/", headers={"Authorization": "Bearer " + Central.usertoken})
        for form in form_response.json():
            if form ["enketoOnceId"] == selectedForm:
                selectedFormName = form["name"]
                Central.form_name = selectedFormName
        try:
            response = requests.get(c_url+'v1/projects/'+str(project_id)+'/forms/'+ selectedFormName+'.xml', headers ={"Authorization": "Bearer " + Central.usertoken})
        except:
            self.iface.messageBar().pushCritical(self.tag,self.tr("Invalid url,username or password"))
            return
        if response.status_code==200:
            xml=response.content
            self.layer_name,self.version, self.geoField,self.fields= self.updateLayerXML(layer,xml)
            layer.setName(self.layer_name)
            self.collectData(layer,selectedForm,doImportData,self.layer_name,self.version,self.geoField)
        else:
            self.iface.messageBar().pushWarning(self.tag,self.tr("not able to connect to server"))


    def flattenValues(self, nestedDict):
        """Reformats a nested dictionary into a flattened dictionary

        If the argument parent_key and sep aren't passed in, the default underscore is used

        Parameters
        ----------
        d: nested dictionary
            ex. {'geotrace_example': {'type': 'LineString', 'coordinates': [[-98.318627, 38.548165, 0]}}

        Returns
        ------
        dict(items) - dictionary
            ex. {'type': 'LineString', 'coordinates': [[-98.318627, 38.548165, 0]}
        """

        new_dict = {}
        for rkey,val in nestedDict.items():
            key = rkey
            if isinstance(val, dict):
                new_dict.update(self.flattenValues(val))
            else:
                new_dict[key] = val
        return new_dict

    def prepareSendForm(self,layer):
#        get the fields model like name , widget type, options etc.
        self.updateFields(layer)
        version= str(datetime.date.today())
        fieldDict= self.getFieldsModel(layer)
        surveyDict= {"name" : layer.name(),"title" : layer.name(),"VERSION" : version, "instance_name" : 'uuid()', "submission_url" : '',
        "default_language" : 'default', 'id_string' : layer.name(), 'type' : 'survey', 'children' : fieldDict}
        self.print(str(surveyDict))
        survey=create_survey_element_from_dict(surveyDict)
        try:
            xml=survey.to_xml(validate=None, warnings='warnings')
            os.chdir(os.path.expanduser('~'))
            self.sendForm(layer.name(),xml)
        except Exception as e:
            self.print("error in creating xform xml",e)
            self.iface.messageBar().pushCritical(self.tag,self.tr("Survey form can't be created, check layer name"))


    def sendForm(self,xForm_id,xml):
#        step1 - verify if form exists:
        formList, response = self.getFormList()
        if not response:
            self.iface.messageBar().pushCritical(self.tag,self.tr("Can not connect to server"))
            return status
        form_key=xForm_id in formList
        message =''
        if form_key:
            message= 'Form Updated'
            method = 'POST'
            #url = self.getValue('url')+'/v1'+'/forms'
            url = self.getValue('url')+'v1/projects/' + str(Central.project_id) + '/forms?ignoreWarnings=true&publish=true'
        else:
            message= 'Created new form'
            method = 'POST'
            url = self.getValue('url')+'v1/projects/' + str(Central.project_id) + '/forms?ignoreWarnings=true&publish=true'
#        method = 'POST'
#        url = self.getValue('url')+'//formUpload'
        #step1 - upload form: POST if new PATCH if exixtent
        with open('xForm.xml','w')as xForm:
            xForm.write(xml)
        authentication = {
            "email": self.getValue(self.tr("user")),
            "password": self.getValue(self.tr("password"))

        }
        authURL = self.getValue('url') + 'v1/sessions'
        authHeaders = {'Content-Type':"application/json"}
        authRequest = requests.post(authURL,data = json.dumps(authentication), headers = authHeaders)
        bearerToken = authRequest.json()["token"]
        headers = {'Content-Type': "application/xml", 'Authorization': "Bearer " + bearerToken}
        response = requests.post(url,data=xml, proxies = self.getProxiesConf(),headers=headers,verify=False)
        if response.status_code== 201 or response.status_code == 200:
            self.iface.messageBar().pushSuccess(self.tr("QRealTime plugin"),
                                                self.tr('Layer is online('+message+'), Collect data from App'))
        elif response.status_code == 409:
            self.iface.messageBar().pushWarning(self.tr("QRealTime plugin"),self.tr("Form exist and can not be updated"))
        else:
            self.iface.messageBar().pushCritical(self.tr("QRealTime plugin"),self.tr("Form is not sent "))
        return response


    def getFieldsModel(self,currentLayer):
        fieldsModel = []
        g_type= currentLayer.geometryType()
        fieldDef={'name':'GEOMETRY','type':'geopoint','bind':{'required':'true()'}}
        fieldDef['Appearance']= 'maps'
        if g_type==0:
            fieldDef['label']='add point location'
        elif g_type==1:
            fieldDef['label']='Draw Line'
            fieldDef['type']='geotrace'
        else:
            fieldDef['label']='Draw Area'
            fieldDef['type']='geoshape'
        fieldsModel.append(fieldDef)
        i=0
        for field in currentLayer.fields():
            widget =currentLayer.editorWidgetSetup(i)
            fwidget = widget.type()
            if (fwidget=='Hidden'):
                i+=1
                continue

            fieldDef = {}
            fieldDef['name'] = field.name()
            fieldDef['map'] = field.name()
            fieldDef['label'] = field.alias() or field.name()
            fieldDef['hint'] = ''
            fieldDef['type'] = self.QVariantToODKtype(field.type())
            fieldDef['bind'] = {}
#            fieldDef['fieldWidget'] = currentFormConfig.widgetType(i)
            fieldDef['fieldWidget']=widget.type()
            self.print('getFieldModel',fieldDef['fieldWidget'])
            if fieldDef['fieldWidget'] in ('ValueMap','CheckBox','Photo','ExternalResource'):
                if fieldDef['fieldWidget'] == 'ValueMap':
                    fieldDef['type']='select one'
                    valueMap=widget.config()['map']
                    config={}
                    for value in valueMap:
                        for k,v in value.items():
                                config[v]=k
                    self.print('configuration is ',config)
                    choicesList=[{'name':name,'label':label} for name,label in config.items()]
                    fieldDef["choices"] = choicesList
                elif fieldDef['fieldWidget'] == 'Photo' or fieldDef['fieldWidget'] == 'ExternalResource' :
                    fieldDef['type']='image'
                    self.print('got an image type field')

#                fieldDef['choices'] = config
            else:
                fieldDef['choices'] = {}
            if fieldDef['name'] == 'ODKUUID':
                fieldDef["bind"] = {"readonly": "true()", "calculate": "concat('uuid:', uuid())"}
            fieldsModel.append(fieldDef)
            i+=1
        return fieldsModel

    def updateLayerXML(self,layer,xml):
        geoField=''
        ns='{http://www.w3.org/2002/xforms}'
        nsh='{http://www.w3.org/1999/xhtml}'
        root= ET.fromstring(xml)
        #key= root[0][1][0][0].attrib['id']
        layer_name=root[0].find(nsh+'title').text
        instance=root[0][1].find(ns+'instance')
        fields={}
        #topElement=root[0][1][0][0].tag.split('}')[1]
        try:
            version=instance[0].attrib['version']
        except:
            version='null'
#        self.print('form name is '+ layer_name)
#        self.print (root[0][1].findall(ns+'bind'))
        for bind in root[0][1].findall(ns+'bind'):
            attrib=bind.attrib
            self.print (attrib)
            fieldName= attrib['nodeset'].split('/')[-1]
            try:
                fieldType=attrib['type']
            except:
                continue
            fields[fieldName]=fieldType
#            self.print('attrib type is',attrib['type'])
            qgstype,config = self.qtype(attrib['type'])
#            self.print ('first attribute'+ fieldName)
            inputs=root[1].findall('.//*[@ref]')
            if fieldType[:3]!='geo':
                #self.print('creating new field:'+ fieldName)
                isHidden= True
                if fieldName=='instanceID':
                    fieldName='ODKUUID'
                    fields[fieldName]=fieldType
                    isHidden= False
                for input in inputs:
                    if fieldName == input.attrib['ref'].split('/')[-1]:
                        isHidden= False
                        break
                if isHidden:
                    self.print('Reached Hidden')
                    config['type']='Hidden'
            else:
                geoField=fieldName
                self.print('geometry field is =',fieldName)
                continue
            self.updateFields(layer,fieldName,qgstype,config)
        return layer_name,version,geoField,fields

    def getTable(self,task):
        """Retrieves data from form table, and filters out only the necessary fields

        Returns
        ------
        response, list
            response1 - HTTP response
                response containing original form table data
            table - list
                contains filtered fields
        """

        user=self.getValue(self.tr("user"))
        password=self.getValue(self.tr("password"))
        requests.packages.urllib3.disable_warnings()
        # hard coded url is being used
        url=self.getValue('url')
        self.print(url)
        storedGeoField = self.geoField
        lastSub=""
        if not self.isImportData:
            try:
                lastSub=self.getValue(self.tr('last Submission'))
            except:
                self.print("error")
        url_submissions=url + "v1/projects/"+str(Central.project_id)+"/forms/" + Central.form_name
        url_data=url + "v1/projects/"+str(Central.project_id)+"/forms/" + Central.form_name + ".svc/Submissions"
        #self.print('urldata is '+url_data)
        response = requests.get(url_submissions, headers={"Authorization": "Bearer " + Central.usertoken, "X-Extended-Metadata": "true"})
        response1 = requests.get(url_data, headers={"Authorization": "Bearer " + Central.usertoken})
        submissionHistory=response.json()
        # json produces nested dictionary contain all table data
        data=response1.json()
        self.print(data)
        subTimeList=[]
        table=[]
        if submissionHistory['submissions']==0:
            return response1, table
        for submission in data['value']:
            formattedData = self.flattenValues(submission)
            formattedData[storedGeoField] = formattedData.pop('coordinates')
            formattedData['ODKUUID'] = formattedData.pop('__id')
            subTime = formattedData['submissionDate']
            subTime_datetime=datetime.datetime.strptime(subTime[0: subTime.index('.')],'%Y-%m-%dT%H:%M:%S')
            subTimeList.append(subTime_datetime)
            stringversion = ''
            coordinates = formattedData[storedGeoField]
            # removes brackets to format coordinates in a string separated by spaces (ex. "38.548165 -98.318627 0")
            if formattedData['type'] == 'Point':
                latitude = coordinates[1]
                coordinates[1] = coordinates[0]
                coordinates[0] = latitude
                for val in formattedData[storedGeoField]:
                    stringversion+= str(val) + ' '
            else:
                count = 1
                for each_coor in coordinates:
                    temp = ""
                    #converting current (longitude, latitude) coordinate to (latitude, longitude) for accurate graphing
                    latitude = each_coor[1]
                    each_coor[1] = each_coor[0]
                    each_coor[0] = latitude
                    for val in each_coor:
                        temp += str(val) + " "
                    stringversion += str("".join(temp.rstrip()))
                    if count != len(coordinates):
                        stringversion += ";"
                    count+=1
            formattedData[storedGeoField] = stringversion
            if formattedData['attachmentsPresent']>0:
                url_data1 = url + "v1/projects/"+str(Central.project_id)+"/forms/" + Central.form_name +"/submissions"+"/"+formattedData['ODKUUID']+ "/attachments"
                self.print("making attachment request"+url_data1)
                attachmentsResponse = requests.get(url_data1, headers={"Authorization": "Bearer " + Central.usertoken})
                self.print("url response is"+ str(attachmentsResponse.status_code))
                for attachment in attachmentsResponse.json():
                    binar_url= url_data1 +"/"+str(attachment['name'])
            #subTime_datetime=datetime.datetime.strptime(subTime,'%Y-%m-%dT%H:%M:%S')
            #subTimeList.append(subTime_datetime)
            for key in list(formattedData):
                self.print(key)
                if key == self.geoField:
                    self.print (self.geoField)
                    continue
                if key not in self.fields:
                    formattedData.pop(key)
                else:
                    if self.fields[key]=="binary":
                        formattedData[key]=binar_url
            self.print("submission parsed"+str(formattedData))
            table.append(formattedData)
        if len(subTimeList)>0:
            lastSubmission=max(subTimeList)
            lastSubmission=datetime.datetime.strftime(lastSubmission,'%Y-%m-%dT%H:%M:%S')+"+0000"
            self.getValue(self.tr('last Submission'),lastSubmission)
        return {'response':response1, 'table':table,'lastID':lastSubmission}
