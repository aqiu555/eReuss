"""Process 1D gel images


"""

from scipy.optimize import minimize_scalar,minimize
from skimage import io
import numpy as np
import matplotlib.pyplot as plt


def band_profile(band,image):
    """returns profile for band"""
    return np.average(image[:,band[0]:band[1]],axis=1)

def iterative_baseline(vec,degree):
    """computes baseline with a polynomial of specified degree
       iterates selecting near points to convergence.

       See:
       Gan, Feng, Guihua Ruan, and Jinyuan Mo.
       "Baseline correction by improved iterative polynomial
       fitting with automatic threshold."
       Chemometrics and Intelligent Laboratory Systems
       82.1 (2006): 59-65.
    """
    yscale = np.max(vec)    
    xs = np.linspace(0,1,len(vec))
    ys = vec/yscale
    old_pys = ys
    while True:
        poly = np.polyfit(xs,ys,degree)
        p_ys = np.polyval(poly,xs)
        mask = p_ys<ys
        ys[mask] = p_ys[mask]
        rho = np.linalg.norm(p_ys-old_pys)/ \
              np.linalg.norm(p_ys)
        if rho<0.001:
            return p_ys*yscale   
    
    
def gauss_curve(x, a, b, c):
    return a* np.exp(-np.power(x - b, 2.) / c)
    
def gaussian_cost(x, xs, ys, a, b):
    curve = gauss_curve(xs, a, b, x)
    residual = ys-curve
    cost = 0.01*sum(np.power(residual[residual>0],2))+\
           sum(np.power(residual[residual<0],2))
    return cost
    
    
def gaussian_peaks(profile, num_peaks=4,min_height=0):
    """find peaks by fitting gaussian curves"""
    peaks = []
    xvals = range(len(profile))
    current = np.copy(profile)
    for p in range(num_peaks):
        b = np.argmax(current)
        a = current[b]
        if a<min_height:
            break
        try:
            res = minimize_scalar(gaussian_cost,args=(xvals,current,a,b))            
        except RuntimeError:
            break
        fit = gauss_curve(xvals,a,b,res.x)        
        area = np.sum(fit)
        peaks.append((a,b,res.x,area))
        current = current-fit            
    return peaks
        

def profiles_and_baselines(bands,image, min_hei, num_gaussians, 
                           bl_degree, smoothing=0):
    """return list of profiles and list of baseline values"""
    profiles = []
    for b in bands:        
        bf = band_profile(b,image)
       
        ys = iterative_baseline(bf,bl_degree)
        if smoothing>0:
            #bf = savitzky_golay(bf,window_size=smoothing*2+1, order=4)
            vals = np.convolve(bf-ys, np.ones((smoothing,))/smoothing, mode='same')
        else:
            vals = bf-ys
        peaks = gaussian_peaks(vals, num_gaussians,min_hei)
        profiles.append((bf,ys,peaks,b))
    return profiles

def calc_peaks(profile,lane_start=0):
    """return list of bands with list of tuples for top, volume, height"""
    band_peaks = []
    for p in profile:
        bf,ys,peaks,b = p
        peak_vols = []
        for k in peaks:
            peak_vols.append((k[1]-lane_start,k[3],k[0]))
        band_peaks.append(peak_vols)
    return band_peaks
        

def peak_table(peak_vols, length_scale=None, length_unit='pixels'):
    table = """
    <table class="result">
    <tr><th>Lane</th><th>Position({0})</th><th>Height</th><th>Area</th></tr>
    """.format(length_unit)
    for ix, pv in enumerate(peak_vols):
        for p in pv:
            table = table+'<tr><td>{0}</td>'.format(ix)
            if length_scale is None:
                val = str(p[0])
            else:
                val = "{0:.2f}".format(p[0]*length_scale)
            table = table+'<td>{0}</td>'.format(val)
            table = table+'<td>{0:.2f}</td>'.format(p[2])
            table = table+'<td>{0:.2f}</td></tr>\n'.format(p[1])
    table = table +'</table>'
    return table
            
        

def report_peaks(peak_vols, file_name, length_scale=None, length_unit='pixels'):
    positions = ['Positions ('+length_unit+')\n']
    vols = ['Areas\n']
    heights = ['Heights\n']
    for ix, pv in enumerate(peak_vols):
        spos = str(ix)+'\t'
        svols = spos
        shis = spos
        for p in pv:
            if length_scale is None:
                spos = spos + str(p[0])+'\t'
            else:
                spos = spos + "{0:.2f}".format(p[0]*length_scale)+'\t'                
            svols = svols + str(p[1])+'\t'
            shis = shis + str(p[2])+'\t'
        positions.append(spos+'\n')
        vols.append(svols+'\n')
        heights.append(shis+'\n')
    ofil = open(file_name,'w')
    ofil.writelines(positions)
    ofil.writelines(heights)
    ofil.writelines(vols)
    ofil.close()
    
def x_profile(original,bl_degree):
    """profile projected into the x axis, corrected by baseline"""
    ## remove background noise for band identification        
    img = original.astype(float)-np.percentile(original,50)  ## background
    img[img<0]=0
    img = img/np.max(img)
    ##aver = (np.max(img,axis = 0)+np.average(img,axis=0))/2
    aver = np.average(img,axis=0)
    bl = iterative_baseline(aver, bl_degree)
    aver = aver-bl
    aver[aver<0]=0
    aver = aver/np.max(aver)
    return aver
   

def find_n_bands(original,band_count,bl_degree):
    """Return list of (x1,x2) tuples with x coordinates of each band"""
    aver = x_profile(original,bl_degree)
    tot_sum = np.sum(aver)
    
    maxwid = len(aver)/band_count    
    best = (0,maxwid,(len(aver)-maxwid*band_count)/2)
    bands = None
    most_diff = 0
    
    for gap in range(1,maxwid/3):
        for offset in range(1,maxwid/3):
            available = (len(aver)-offset-gap*(band_count-1))/band_count
            for wid in range(maxwid/3,available):
                tot = 0
                for b in range(band_count):
                    x1 = offset+b*gap+b*wid
                    x2 = x1+wid
                    tot = tot + np.sum(aver[x1:x2])
                diff = float(tot)/wid/band_count-\
                       float(tot_sum-tot)/(1+gap*(band_count-1)+offset)
                if diff>most_diff:
                    most_diff = diff
                    best = (gap,offset,wid)
                    
    bands = []
    gap,offset,wid = best
    for b in range(band_count):
        x1 = offset+b*gap+b*wid
        x2 = x1+wid
        bands.append((x1,x2))
    
    return bands,aver

def save_band_profile(aver,bands,save_image):
    test = np.zeros(len(aver))
    plt.figure(figsize=(10,3))
    for b in bands:
        test[b[0]:b[1]] = 0.5
    plt.plot(range(len(aver)),aver)
    plt.plot(np.arange(len(test)),test)
    plt.gca().axes.get_yaxis().set_visible(False)   
    plt.axis([0,len(aver),0,1])
    plt.savefig(save_image,dpi=200,bbox_inches='tight')
    plt.close()       


def plot_band_peaks(band_profiles,out_file,start_line=-1,debug = True):
    """plot band peaks and save to out_file
       if debug is True, also plots the original along the baselines
    """
    b,ys,peaks,bands = band_profiles[0]
    plot_scale = max(b)
    xs = range(len(ys))

    if debug:
        plt.figure(figsize=(10,8))                
        for ix,b_ys in enumerate(band_profiles):
            b,ys,peaks,bands = b_ys
            bl = b/plot_scale+ix+1
            plt.plot(xs,bl,'-k',linewidth=3)
            plt.plot(xs,ys,'-r')            
        plt.savefig(out_file+'_debug.png',dpi=200)
        plt.close()

    # plot band profiles subtracting baseline
    plt.figure(figsize=(10,8))                
    for ix,b_ys in enumerate(band_profiles):
        b,ys,peaks,bands = b_ys
        bl = (b-ys)/plot_scale+ix+1
        plt.plot(xs,bl,'-k',linewidth=3)
        for p in peaks:      
            plt.plot(xs,gauss_curve(xs,p[0]/plot_scale,p[1],p[2])+ix+1,'-r')
            plt.plot([p[1],p[1]],[ix+1+p[0]/plot_scale,ix+1+p[0]/plot_scale+0.2],
                     '-r',linewidth=3)
    if start_line>=0:
        plt.plot([start_line,start_line],[0,len(band_profiles)+1],'-g',linewidth=3)
    plt.savefig(out_file,dpi=200)
    plt.close()

def load_image(input_image,channel='average',invert='auto'):
    orig = io.imread(input_image).astype(float)       
    if len(orig.shape)>2:
        tot = np.zeros(orig.shape[:2])
        for ix, col in enumerate(['red','green','blue']):
            if channel !=col:
                tot = tot + orig[:,:,ix]
        orig = tot
        
    print channel, invert
    orig = orig-np.min(orig)
    orig = orig/np.max(orig)
    if invert == 'yes' or (invert=='auto' and np.average(orig)>0.5):
        orig=1-orig
    return orig



def langmuir_cost(k,ratios,mobilities):
    kr = k*ratios
    preds = kr/(1+kr)
    cost = np.sum((mobilities-preds)**2)
    return cost    

def langmuir(ratios,mobility):
    """return normalized mobility, Keq and max_mob"""
    max_mob = np.max(mobility)
    mobs = (max_mob-mobility)/max_mob    
    res = minimize_scalar(langmuir_cost,args=(ratios,mobs))
    print res.fun
    return mobs,res.x,res.fun
    
def plot_langmuir(file_name,mobs,ratios,keq):
    plt.figure(figsize=(10,8))                
    plt.plot(ratios,mobs,'xb')
    xs = np.linspace(0,np.max(ratios)*1.1,200)
    kr = keq*xs
    ys = kr/(1+kr)
    plt.plot(xs,ys,'-k')
    plt.savefig(file_name,dpi=200)
    plt.close()
    
    
def hill_cost(x,ratios,mobilities):
    ln = np.power(ratios[ratios>0],x[0])
    preds = ln/(x[1]+ln)
    print preds
    cost = np.sum((mobilities[ratios>0]-preds)**2)
    return cost    

def hill(ratios,mobility):
    """return normalized mobility, Keq and max_mob"""
    max_mob = np.max(mobility)
    mobs = (max_mob-mobility)/max_mob    
    res = minimize(hill_cost,[1,0.5],args=(ratios,mobs))
    print res.fun
    return mobs,res.x,res.fun
    
def plot_hill(file_name,mobs,ratios,n,k):
    plt.figure(figsize=(10,8))                
    plt.plot(ratios,mobs,'xb')
    xs = np.linspace(1,np.max(ratios)*1.1,200)
    ln = np.power(xs,n)
    ys = ln/(k+ln)
    plt.plot(xs,ys,'-k')
    plt.savefig(file_name,dpi=200)
    plt.close()
    