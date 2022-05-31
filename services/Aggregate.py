from helper.layer2form import layer2XForm
from .Service import Service
import os
import requests
import xml.etree.ElementTree as ET
import six
from pyxform.builder import create_survey_element_from_dict

class Aggregate (Service):
    tag='ODK Aggregate'
    def __init__(self,parent,caller):
        super(Aggregate, self).__init__(parent, caller)
        self.tag='ODK Aggregate'

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