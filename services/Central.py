from .Service import Service
import os
import requests
import datetime
import site
import json
import xml.etree.ElementTree as ET
from pyxform.builder import create_survey_element_from_dict

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

    def getServiceName(self):
        return "Central"

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
        survey= create_survey_element_from_dict(surveyDict)
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
