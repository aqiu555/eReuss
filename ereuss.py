"""Encapsulate eReuss processor
   ----------------------------
   Ferdinand Frederic Reuss , 1807, discovery of the electrokinetic phenomenon      

"""

import gel1d as gel
from skimage.transform import rotate
import numpy as np
import zipfile
import xml.etree.cElementTree as ET


def array_as_csv(array):
    res = ''
    for x in array:
        res = res+str(x)+';'
    return res[:-1]




#TODO(LK): refactoring, bands should be called lanes and peaks should be bands

class BandProfiler(object):
    """Encapsulates code for band detection and profiling"""
    
    band_export = [('band_degree','Degree for band baseline'),
                   ('lane_count','Used wells'),
                   ('band_text',None,20,40),
                   ('band_x_text',None,20,8)]
    
    band_template= """
    <table class="controls">
    <tr><td>[lane_count]</td></tr>
    <tr><td>[band_degree]</td></tr>
    </table><table class="controls">
    <tr><span style="width:20%"><td>X vals</td></span>
    <span style="width:80%"><td>Bands</td></span></tr>
    <tr><span style="width:20%"><td>[band_x_text]</td></span>
    <span style="width:80%"><td>[band_text]</td></span></tr>
    </table>"""
                   
    peak_export = [('peak_smoothing','Smoothing (pixels)'),
                   ('num_gaussians','Number of Gaussians'),
                   ('min_peak_height','Minimum height (%)'),
                   ('baseline_degree','Degree for baseline')]
    
    peak_template= """
    <table class="controls">
    <tr><td>[peak_smoothing]</td></tr>
    <tr><td>[baseline_degree]</td></tr>        
    <tr><td>[min_peak_height]</td></tr>
    <tr><td>[num_gaussians]</td></tr>
    </table>"""
    
            
                
    def __init__(self):
        self.band_text = ''
        self.band_text_back = ''
        self.band_x_text = ''
        self.band_x_text_back = ''
        self.band_x_vals = None
        self.band_degree = 5
        self.min_peak_height = 10
        self.peak_smoothing = 0
        self.baseline_degree = 1
        self.bands = None
        self.profile = None
        self.band_profiles = None
        self.lane_count = 10
        self.num_gaussians = 1        
        self.scale = None
        self.units = 'pixels'
        self.lane_start = 0
        
    def build_band_text(self):
        self.band_text=''
        for b in self.bands:
            self.band_text = self.band_text + '{0}:{1}\n'.format(b[0],b[1])
        self.band_text_back = self.band_text        
        
    def check_x_vals(self):
        if self.band_x_vals is not None and len(self.band_x_vals)!=len(self.bands):
            self.band_x_vals = None
            self.band_x_text = ''
            self.band_x_text_back = ''
        
    def build_bands_from_text(self):
        lines = self.band_text.strip().split('\n')
        self.bands = []
        for line in lines:
            edges = line.split(':')
            self.bands.append((int(edges[0]),int(edges[1])))
        self.check_x_vals()
        
    def find_bands(self,image,save_file=None):
        if self.band_text_back == self.band_text:
            self.bands,self.profile = gel.find_n_bands(image,
                                      self.lane_count,
                                      self.band_degree)
            self.build_band_text()
            self.band_text_back = self.band_text
        else:
            self.build_bands_from_text();
        
        if save_file is not None:
            gel.save_band_profile(self.profile,self.bands,save_file)        
        
        if self.band_x_text != self.band_x_text_back:
            self.band_x_text_back = self.band_x_text
            self.band_x_vals=[]
            for val in self.band_x_text.strip().split('\n'):
                self.band_x_vals.append(float(val))                
        self.check_x_vals()
    
    def find_peaks(self,image):
        self.band_profiles = gel.profiles_and_baselines(
                                           self.bands,
                                           image,                                          
                                           self.min_peak_height*0.01,   
                                           self.num_gaussians,
                                           self.baseline_degree,
                                           self.peak_smoothing)
        self.peak_vols = gel.calc_peaks(self.band_profiles,self.lane_start) 
        
    
    def compute_scale(self,band_sep):
        if len(self.bands)>1:
            b1 = self.bands[0]
            b2 = self.bands[1]
            dist = b2[0]-b1[0]
            self.scale = float(band_sep)/dist
            self.units = 'cm'        
        else:
            self.scale = 1.0
            self.units = 'pixels'        
            
        
    
    def report_peaks(self,out_image,out_report):
        gel.plot_band_peaks(self.band_profiles,out_image,self.lane_start)        
        gel.report_peaks(self.peak_vols,out_report,self.scale,self.units)    
        
    def peak_table(self):
        return gel.peak_table(self.peak_vols,self.scale,self.units)
    
    def langmuir(self,file_name):
        """compute langmuir and save plot if possible"""
        if self.band_x_vals is not None and len(self.band_x_vals)==len(self.peak_vols):
            ratios = np.array(self.band_x_vals)            
            mobs = []
            for b in self.peak_vols:
                if len(b)==0:
                    return None
                else:
                    mobs.append(b[0][0])
            mobs = np.array(mobs).astype(float)           
            norm_mobs, keq, err= gel.langmuir(ratios,mobs)            
            gel.plot_langmuir(file_name,norm_mobs,ratios,keq)
            return keq,err
        else:
            return None
            
    def hill(self,file_name):
        """compute hill curve and save plot if possible"""
        if self.band_x_vals is not None and len(self.band_x_vals)==len(self.peak_vols):
            ratios = np.array(self.band_x_vals)            
            mobs = []
            for b in self.peak_vols:
                if len(b)==0:
                    return None
                else:
                    mobs.append(b[0][0])
            mobs = np.array(mobs).astype(float)           
            norm_mobs, x, err = gel.hill(ratios,mobs)            
            gel.plot_hill(file_name,norm_mobs,ratios,x[0],x[1])
            return x[0],x[1],err
        else:
            return None

        

class EReuss(object):
    """Encapsulates all the code for processing one gel"""
    
    export_process = [('well_x1','ROI x1'),
                      ('well_y1','ROI y1'),
                      ('well_x2','ROI x2'),
                      ('well_y2','ROI y2'),
                      ('well_count','Well count'),
                      ('comb_length','Comb length (cm)'),
                      ('lane_length','Lane end'),
                      ('lane_start','Lane start'),
                      ('lane_count','Used wells')]
                      
                    
    process_template= """
    <table class="controls">
    <tr><td>[comb_length]</td><td> </td></tr>
    <tr><td>[well_count]</td><td>[lane_count]</td></tr>        
    <tr><td>[well_x1]</td><td>[well_y1]</td></tr>
    <tr><td>[well_x2]</td><td>[well_y2]</td></tr>    
    <tr><td>[lane_start]</td><td>[lane_length]</td></tr>        
    </table>"""
    
    export_load = [('invert','Invert image'),
                   ('color','Band color')]
                   
    droplists = {'invert':['auto','yes','no'],
                 'color':['red','green','blue','average']}
    
    load_template= """
    <table class="controls">
    <tr><td>[color]</td></tr>
    <tr><td>[invert]</td></tr>
    </table>"""
        
    export_report = [('base_file_name','Report name'),
                     ('voltage','Voltage'),
                     ('time','Time')]
    
    report_template= """
    <table class="controls">
    <tr><td>[base_file_name]</td><td></td></tr>
    <tr><td>[voltage]</td><td>[time]</td></tr>
    
    
    </table>"""
    
    def __init__(self):
        """
        """
        #loading
        self.invert = 'auto'
        self.color = 'average'
        #processing        
        self.comb_length = 0.0
        self.well_count = 0
        self.well_x1 = 0
        self.well_x2 = 0
        self.well_y1 = 0
        self.well_y2 = 0
        self.lane_length = 0
        self.lane_start = 0
        self.lane_count = 15
        self.original = None
        self.processed = None        
        
        self.base_file_name = 'report'
        self.voltage = 0.0
        self.time = 0.0
        self.langmuir = None
        self.hill = None

    def check_bounds(self,x1,x2,upper):
        if x1 < 0:
            x1 = 0                
        if x1 >= upper:
            x1 = upper-1
        if x2 < 0:
            x2 = 0
        if x2 >=upper:
            x2 = upper-1
        
        return x1,x2
        
        
    def load_image(self,file_name):
        """initialise the frame manager with thelisted images
        """
        self.original = gel.load_image(file_name,
                                       self.color,
                                       self.invert)
        self.well_x1 = 0
        self.well_x2 = self.original.shape[1]
        self.well_y1 = 0
        self.well_y2 = 0
        self.lane_start = 0
        self.lane_length = self.original.shape[0]               
        self.processed = None   
        self.band_profiler = BandProfiler()
        
        
        
    def transform_image(self):
        """apply transformations to create processed image"""
        self.well_x1,self.well_x2 = self.check_bounds(self.well_x1,
                                                      self.well_x2,
                                                      self.original.shape[1])
        self.well_y1,self.well_y2 = self.check_bounds(self.well_y1,
                                                      self.well_y2,
                                                      self.original.shape[0])        
        angle = np.angle(np.complex(self.well_x2-self.well_x1,
                                    self.well_y2-self.well_y1),True)
        img = rotate(self.original,angle, resize=True)
        top = (self.well_y1 + self.well_y2 + img.shape[0]-self.original.shape[0])/2
        bottom = top + self.lane_length
        left = self.well_x1 + (img.shape[1]-self.original.shape[1])/2
        right = self.well_x2 + (img.shape[1]-self.original.shape[1])

        self.processed = img[top:bottom,left:right]
        self.processed = self.processed-np.min(self.processed)/np.max(self.processed)
        
        self.band_profiler.lane_count = self.lane_count
                             
    def find_bands(self,save_file=None):
        self.band_profiler.find_bands(self.processed,save_file)

    def build_report(self,image,csv):
        if self.well_count>1 and self.comb_length>0:
            self.band_profiler.compute_scale(float(self.comb_length)/(self.well_count-1))
        self.band_profiler.lane_start = self.lane_start
        self.band_profiler.find_peaks(self.processed)
        self.band_profiler.report_peaks(image,csv)
        self.langmuir = self.band_profiler.langmuir('html/langmuir.png')
        if self.langmuir is not None:
            fil = open(csv,'a')
            fil.write('\nLangmuir:\nKeq = {0}\nError =  {1}\n'.format(self.langmuir[0],self.langmuir[1]))
            fil.close()
        
        self.hill = self.band_profiler.hill('html/hill.png')                
        if self.hill is not None:
            fil = open(csv,'a')
            fil.write('\nHill:\nN = {0}\nKeq = {1}\nError =  {2}\n'.format(
                          self.hill[0],self.hill[1],self.hill[2]))
            fil.close()
        
        
    def save_profiles(self,file_name):    
        """save all profile data to text file
        """
        root = ET.Element("root")
        doc = ET.SubElement(root, "doc")
        ET.SubElement(doc,
                      "params",
                      scale=str(self.band_profiler.scale),
                      units=self.band_profiler.units)

        ET.SubElement(doc,
                      "clip",
                      x1=str(self.well_x1),
                      y1=str(self.well_y1),
                      x2=str(self.well_x2),
                      y2=str(self.well_y2),
                      length=str(self.lane_length),
                      start=str(self.lane_start))
                     
        for ix,b_ys in enumerate(self.band_profiler.band_profiles):
            band_el = ET.SubElement(doc, "band", name=str(ix))
            if self.band_profiler.band_x_vals is not None:
                band_el.text=str(self.band_profiler.band_x_vals[ix])
            vals,baseline,peaks,bands = b_ys
            ET.SubElement(band_el, "values").text = array_as_csv(vals)
            ET.SubElement(band_el, "baseline").text = array_as_csv(baseline)
            for ix,peak in enumerate(peaks):
                ET.SubElement(band_el,
                              "peak",
                              name=str(ix),
                              a = str(peak[0]),
                              b = str(peak[1]),  
                              c = str(peak[2]),  
                              area = str(peak[3]))    
        tree = ET.ElementTree(root)
        tree.write(file_name)
           
        
    
    def archive_report(self,path):
        self.base_file_name = self.base_file_name.replace(' ','_')
        zf = zipfile.ZipFile(path+self.base_file_name+'.zip', 'a')
        self.save_profiles(path+self.base_file_name+'.xml')
        zf.write(path+'image.png','image.png')
        zf.write(path+'bands.png','bands.png')
        zf.write(path+self.base_file_name+'.xml',self.base_file_name+'.xml')
        zf.write(path+'bands.csv',self.base_file_name+'.csv')
        if self.langmuir is not None:
            zf.write(path+'langmuir.png','langmuir.png')
        if self.hill is not None:
            zf.write(path+'hill.png','hill.png')
            
        return self.base_file_name+'.zip'
        
        
