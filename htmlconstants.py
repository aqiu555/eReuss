"""
    Constants and utilities for rendering html pages
    
    attributes_to_form formats:
        the list of tuples containing the attribute name and label can optionally
        have 2 other attributes, rows and columns, forcing textarea
"""
import string

SERVER_URL='http://127.0.0.1:8081'
"""str: url for the server"""

HTML_FOLDER = 'html/'
START_HTML=HTML_FOLDER+'index.html'
LOAD_HTML=HTML_FOLDER+'load.html'
IMAGE_HTML=HTML_FOLDER+'image.html'
BANDS_HTML=HTML_FOLDER+'bands.html'
PEAKS_HTML=HTML_FOLDER+'peaks.html'
REPORT_HTML=HTML_FOLDER+'report.html'



ORIGINAL_IMAGE='original.png'
CURRENT_IMAGE='image.png'
BAND_PROFILE_IMAGE='profile.png'
PEAK_PROFILE_IMAGE='bands.png'
PEAK_PROFILE_CSV='bands.csv'
PEAK_PROFILE_XML='bands.xml'
URL_UPLOAD = '/upload'
"""POST: upload file"""
URL_LOAD_PAGE = '/loadpage'
"""GET: load page"""
URL_LOAD_IMAGE = '/loadimage'
"""POST: load image parameters"""
URL_IMAGE_PAGE = '/image'
URL_CLIP = '/clip'
"""POST: clip image"""
URL_BAND_PAGE = '/bands'
URL_FIND_BANDS = '/findbands'
"""POST: find bands"""

URL_PEAK_PAGE = '/peaks'
URL_FIND_PEAKS = '/findpeaks'
"""POST: update params and find peaks"""


URL_REPORT_PAGE = '/report'

URL_DWNLOAD_REPORT = '/download'


ANGLE = 'ANGLE'
TOP = 'TOP'
LEFT = 'LEFT'
RIGHT = 'RIGHT'
BOTTOM = 'BOTTOM'

HTML_FOLDER_TAG='[HTML]'
"""str: id tag to be replaced by the html folder"""
HTML_FORM_TAG='[FORM]'
HTML_RSULT_TAG = '[RESULT]'

def replace_in_string(source,replacements):
    """
    replace the keys of replacements in source with
    the values of replacements (a dictionary)
    returns the replaced string plus a list of all
    keys not found in the string
    """
    outkeys=[]
    if replacements is not None:
        for key in replacements.keys():            
            if key in source:
                source=string.replace(source,key,replacements[key])
            else:
                outkeys.append(key)
    return source,outkeys

def create_control(control_type,name=None,label=None,options=None):
    """
    return an input control for html
    """
    if label is not None:
        res = '<label for="{1}">{0}:</label><{2} '.format(label,name,control_type)
    else:
        res = '<'+control_type+' '
    if name is not None:
        res = res + 'name="{0}" id="{0}" '.format(name)
    if options is not None:
        res = res + options
    return res + '>\n'.format(control_type,name,options)    
    

def control_dict(obj,attributes,drop_lists):
    """
    return dictionary with html input elements for listed attributes of
    object. Dictionary keys include brackets: [attr_name]
    """    
    replacements = {}        
    for a in attributes:        
        line = ''
        if len(a)==2:
            at_name,at_label = a
            attr = getattr(obj,at_name)                        
            if at_name in drop_lists.keys():            
                line = line + create_control('select',at_name,at_label)
                for option in drop_lists[at_name]:
                    if option == attr:                
                        line = line + create_control('option',None,None,'selected')
                    else:
                        line = line + create_control('option')
                    line = line[:-1] +option +'</option>\n'
                line = line + '</select></p>\n'
            elif type(attr) is bool:
                if attr:
                    check = 'checked'
                else:
                    check = None
                line = line + create_control('input type="checkbox"',at_name,at_label,check)
                # unchecked checkboxes return no value, so this preserves the false
                # because only the first value is used
                line = line + create_control('input type="hidden" value="false"',at_name)
            else:
                line = line + create_control('input type="text" value="{0}"'.format(attr),at_name,at_label)
        else:
            at_name,at_label,rows,cols = a
            attr = getattr(obj,at_name)
            aux = 'textarea rows="{0}" cols="{1}"'.format(rows,cols)
            line = line + create_control(aux,at_name,at_label)
            line = line + attr +'</textarea>\n'
            
        replacements['['+at_name+']']=line
    return replacements
    

def attributes_to_form(name, action,obj,attributes,
                       drop_lists={}, template='', submit = 'Submit'):
    """
    return a string with an html form for all attributes listed
    name is the name of the form
    action is the action url for the form
    obj is any object    
    attributes is a list of tuples for the attributes to include in form
        (attribute name, form label)
    drop_lists is a dictionary with attribute_name and list of strings for
      options
    template is a string where each instance of the name within square brackets
    is replaced by the control      
    """
    
    res = '<form name="{0}" action="{1}" method="post" enctype="multipart/form-data">\n'.format(name,action)
    replacements = control_dict(obj,attributes,drop_lists)
    form,outs = replace_in_string(template,replacements)
    res = res + form
    for out in outs:
        res = res + out
    res = res + '<input type="submit" value="{0}">\n</form>\n'.format(submit)
    return res

def form_to_attributes(form_data,attributes,obj):
    """updates the object attributes with the form data
    form data is a dictionary with attribute names and values
    attributes is a list of tuples for all exported attributes of the class (name, label)
    obj is the object to update.
    """

    for a in attributes:
        at_name = a[0]
        print at_name
        if at_name in form_data.keys():
            attr = getattr(obj,at_name)  
            if type(attr) is bool:
                setattr(obj, at_name, form_data[at_name].upper=='TRUE')
            elif type(attr) is int:
                setattr(obj, at_name, int(form_data[at_name]))
            elif type(attr) is float:
                setattr(obj, at_name, float(form_data[at_name]))
            elif type(attr) is long:
                setattr(obj, at_name, long(form_data[at_name]))
            else:
                setattr(obj, at_name, form_data[at_name])
                    
      
            

def process_html(html_source,replacements=None):
    """reads the html source file and replaces tags
       replacements is a dictionary with tag:text_to_replace
    """
    fil = open(html_source)
    source = fil.read()
    fil.close()
    source=string.replace(source,HTML_FOLDER_TAG,HTML_FOLDER)        

    source,outs = replace_in_string(source,replacements)
    return source
