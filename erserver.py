"""eKlose HTTP server module

This module implements HTTP access to eKlose

HTTP request handling based on examples by Doug Hellmann on
Python Module of the Week:
    http://pymotw.com/2/BaseHTTPServer/index.html
"""

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import urlparse
import htmlconstants as htc
from ereuss import EReuss,BandProfiler
from skimage.io import imsave
import cgi
import os

ereuss = EReuss()
   
class Handler(BaseHTTPRequestHandler):
    
    def send_file(self,file_name,contents):
        """call send_header depending on file_name"""
        mimetype = None
        if file_name.endswith(".html"):
            mimetype='text/html'
        if file_name.endswith(".jpg"):
            mimetype='image/jpg'
        if file_name.endswith(".png"):
            mimetype='image/png'
        if file_name.endswith(".gif"):
            mimetype='image/gif'
        if file_name.endswith(".js"):
            mimetype='application/javascript'
        if file_name.endswith(".css"):
            mimetype='text/css'
        if file_name.endswith(".zip"):
            mimetype='application/zip, application/octet-stream'
        
        if mimetype is not None:
            self.send_response(200)            
            self.send_header('Content-type',mimetype)
            self.end_headers()
            self.wfile.write(contents)            
        return    
    
    def redirect(self,url):
        self.send_response(301)       
        self.send_header('Location',url)
        self.send_header( 'Connection', 'close' );
        self.end_headers()        
    
    def do_GET(self):
        """Process GET requests

        Handles different requests for
            index page 
            file upload page (with id)
            session page (with id)
            other files
        """
        html='Error 404'

        parsed_url = urlparse.urlparse(self.path)
        path = parsed_url[2]
        
        file_name='x.html'

        if path=='/' or path.upper()=='/INDEX.HTML':
            html = htc.process_html(htc.START_HTML)  
        elif path == htc.URL_LOAD_PAGE:
            form = htc.attributes_to_form('loadform',htc.URL_LOAD_IMAGE[1:],
                                          ereuss,EReuss.export_load,
                                          EReuss.droplists,
                                          EReuss.load_template)                
            html = htc.process_html(htc.LOAD_HTML,{htc.HTML_FORM_TAG:form})         
        elif path == htc.URL_IMAGE_PAGE:
            ereuss.load_image(htc.HTML_FOLDER+htc.ORIGINAL_IMAGE)            
            form = htc.attributes_to_form('imageform',htc.URL_CLIP[1:],
                                          ereuss,EReuss.export_process,
                                          {},EReuss.process_template) 
            ereuss.transform_image()
            imsave(htc.HTML_FOLDER+htc.CURRENT_IMAGE,ereuss.processed)
            html = htc.process_html(htc.IMAGE_HTML,{htc.HTML_FORM_TAG:form})            
        elif path == htc.URL_BAND_PAGE:
            ereuss.find_bands(htc.HTML_FOLDER+htc.BAND_PROFILE_IMAGE)
            form = htc.attributes_to_form('bandsform',htc.URL_FIND_BANDS[1:],
                                          ereuss.band_profiler,
                                          BandProfiler.band_export,
                                          {},BandProfiler.band_template)                
            html = htc.process_html(htc.BANDS_HTML,{htc.HTML_FORM_TAG:form})     
        elif path == htc.URL_PEAK_PAGE:
            ereuss.build_report(htc.HTML_FOLDER+htc.PEAK_PROFILE_IMAGE,
                                htc.HTML_FOLDER+htc.PEAK_PROFILE_CSV)
            form = htc.attributes_to_form('peaksform',htc.URL_FIND_PEAKS[1:],
                                          ereuss.band_profiler,
                                          BandProfiler.peak_export,
                                          {},BandProfiler.peak_template) 
            html = htc.process_html(htc.PEAKS_HTML,{htc.HTML_FORM_TAG:form})    
        elif path == htc.URL_REPORT_PAGE:
            result = ereuss.band_profiler.peak_table()
        
            form = htc.attributes_to_form('reportform',htc.URL_DWNLOAD_REPORT[1:],
                                          ereuss,EReuss.export_report,
                                          {},EReuss.report_template) 
            html = htc.process_html(htc.REPORT_HTML,
                                    {htc.HTML_RSULT_TAG:result,
                                     htc.HTML_FORM_TAG:form})      
        else:
            #if a miscelaneous file is requested, it is only read from the HTML_FOLDER        
            html = open(htc.HTML_FOLDER+path.split('/')[-1],'rb').read()    
            file_name=path.split('/')[-1]
            
        self.send_file(file_name,html)    
        return
   
    def save_original_image(self,file_name):
        """Saves the image into the data_path
        https://gist.github.com/UniIsland/3346170#file-simplehttpserverwithupload-py
        """
        
        boundary = self.headers.plisttext.split("=")[1]
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()
        remainbytes -= len(line)
        line = line.split('filename="')[1]
        original_name = line.split('"')[0]
        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)
        try:
            out = open(file_name, 'wb')
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?")
                
        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                preline = preline[0:-1]
                if preline.endswith('\r'):
                    preline = preline[0:-1]
                out.write(preline)
                out.close()
                return (True, original_name)
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpect Ends of data.")
        
        
    def post_data_as_dict(self):
        """
            Return post data as a dictionary 
        """        
        ctype,pdict = cgi.parse_header(self.headers.getheader('Content-type'))
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers['content-length'])
            postvars = urlparse.parse_qs(
                        self.rfile.read(length), 
                        keep_blank_values=1)
        else:
            postvars = {}
        for key in postvars.keys():
            #this is important not only to get rid of lists but
            #because of the hidden input trick for checkboxes
            postvars[key]=postvars[key][0]
        return postvars
        
            
    def handle_post_request(self):
        """Handles file upload and other stuff (WiP...)
           Source: Huang, Tao at https://gist.github.com/UniIsland/3346170
           Returns (True, session_id) if successful, or (False, error_message) otherwise
        """
        url = urlparse.urlparse(self.path)[2]
        if url == htc.URL_UPLOAD:            
            res, msg = self.save_original_image(htc.HTML_FOLDER+htc.ORIGINAL_IMAGE)           
            if res:
                ereuss.base_file_name = os.path.splitext(msg)[0]
                return (True, htc.SERVER_URL+htc.URL_LOAD_PAGE)
            else:
                return (res,msg)
        elif url == htc.URL_LOAD_IMAGE:
            query = self.post_data_as_dict()
            htc.form_to_attributes(query,
                               EReuss.export_load,
                               ereuss)                                                   
            return (True, htc.SERVER_URL+htc.URL_IMAGE_PAGE)
        elif url == htc.URL_CLIP:
            query = self.post_data_as_dict() 
            htc.form_to_attributes(query,
                               EReuss.export_process,
                               ereuss)        
            ereuss.transform_image()
            imsave(htc.HTML_FOLDER+htc.CURRENT_IMAGE,ereuss.processed)                                              
            return (True, htc.SERVER_URL+htc.URL_BAND_PAGE)
        elif url ==htc.URL_FIND_BANDS:
            query = self.post_data_as_dict() 
            htc.form_to_attributes(query,                               
                               BandProfiler.band_export,
                               ereuss.band_profiler)        
            return (True, htc.SERVER_URL+htc.URL_BAND_PAGE)
        elif url ==htc.URL_FIND_PEAKS:
            query = self.post_data_as_dict() 
            htc.form_to_attributes(query,                               
                               BandProfiler.peak_export,
                               ereuss.band_profiler)        
            return (True, htc.SERVER_URL+htc.URL_PEAK_PAGE)
        elif url ==htc.URL_DWNLOAD_REPORT:
            query = self.post_data_as_dict() 
            htc.form_to_attributes(query,                               
                               EReuss.export_report,
                               ereuss) 
            fn = ereuss.archive_report(htc.HTML_FOLDER)
            return (True, htc.SERVER_URL+'/'+fn)
        return(False,'/') 

    def do_POST(self):
        (res,msg)=self.handle_post_request()
        if not res:
            # upload failed
            self.send_response(200)       
            self.end_headers()        
            self.wfile.write('Request failed: %s\n' % msg)
        else:
            #upload OK, redirecting to approapriate page
            self.redirect(msg)
            
        return

    

if __name__ == '__main__':

    #For safety reasons, server is confined to local host
    #Change 'localhost' to '' to enable remote access
    #server = ThreadedHTTPServer(('localhost', 8081), Handler)
    server = HTTPServer(('localhost', 8081), Handler)    
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()
