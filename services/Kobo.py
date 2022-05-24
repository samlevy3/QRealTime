from .Service import Service
import requests
import xml.etree.ElementTree as ET
import json
from pyxform.builder import create_survey_element_from_dict

class Kobo (Service):
    def __init__(self,parent,caller):
        super(Kobo, self).__init__(parent,caller)
        self.tag='Kobo'

    def getServiceName(self):
        return "Kobo"

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
        return payload

    def sendForm(self,layer):
        xForm_id = layer.name()
        payload = self.prepareSendForm(layer)
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