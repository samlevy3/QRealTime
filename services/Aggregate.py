from helper.layer2form import layer2XForm
from .Service import Service
import os
import requests
import datetime
import site
import json
import xml.etree.ElementTree as ET
import six
from pyxform.builder import create_survey_element_from_dict

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

    def getServiceName(self):
        return "Aggregate"

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
    # def prepareSendForm(self,layer):
    #     self.updateFields(layer)
    #     version= str(datetime.date.today())
    #     fieldDict= self.getFieldsModel(layer)
    #     self.print ('fieldDict',fieldDict)
    #     surveyDict= {"name":layer.name(),"title":layer.name(),'VERSION':version,"instance_name": 'uuid()',"submission_url": '',
    #     "default_language":'default','id_string':layer.name(),'type':'survey','children':fieldDict }
    #     survey=create_survey_element_from_dict(surveyDict)
    #     try:
    #         xml=survey.to_xml(validate=None, warnings='warnings')
    #         os.chdir(os.path.expanduser('~'))
    #         self.sendForm(layer.name(),xml)
    #     except Exception as e:
    #         self.print("error in creating xform xml",e)
    #         self.iface.messageBar().pushCritical(self.tag,self.tr("Survey form can't be created, check layer name"))
    def sendForm(self,layer):
        xml = layer2XForm(self, layer)
        xForm_id = layer.name()
        os.chdir(os.path.expanduser('~'))
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