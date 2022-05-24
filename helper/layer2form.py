import datetime
from pyxform.builder import create_survey_element_from_dict


def layer2XForm(self, layer):
# get the fields model like name , widget type, options etc.
    self.updateFields(layer)
    version= str(datetime.date.today())
    fieldDict= self.getFieldsModel(layer)
    surveyDict= {"name" : layer.name(),"title" : layer.name(),"VERSION" : version, "instance_name" : 'uuid()', "submission_url" : '',
    "default_language" : 'default', 'id_string' : layer.name(), 'type' : 'survey', 'children' : fieldDict}
    self.print(str(surveyDict))
    survey= create_survey_element_from_dict(surveyDict)
    try:
        xml=survey.to_xml(validate=None, warnings='warnings')
        return xml
    except Exception as e:
        self.print("error in creating xform xml",e)
        self.iface.messageBar().pushCritical(self.tag,self.tr("Survey form can't be created, check layer name"))

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