# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.PyQt.QtCore import QCoreApplication, QFileInfo, QVariant
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator
from qgis.core import (QgsProject,
                       QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,      
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFile,               
                       QgsProcessingMultiStepFeedback,
                       QgsRasterLayer,                     
                       QgsProcessingParameterString,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterBoolean,
                       QgsProcessingUtils

                       )
from qgis import processing
from pathlib import Path
from ..general_modules import path
import tempfile
import subprocess
import shutil
import re
import os
import datetime



class ProcessLidar(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
  

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ProcessLidar()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'process_lidar'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Procesiraj lidar')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Lidar')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'lidar'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        help_text = """Orodje za procesiranje lidarja z LAStools. 
        Za pravilno delovanje je potrebno imeti naložen LAStools na C:/LAStools!

        Rezultat je DEM ter karta gostote talnih točk (število točk na celico).
        
        """
        return self.tr(help_text)

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFile(
                'infolder', 
                'Mapa z .laz datotekami',
                 behavior=QgsProcessingParameterFile.Folder, 
                 fileFilter='All files (*.*)'
                 )
            )

        
        self.addParameter(
            QgsProcessingParameterString(
                'tile_params', 
                'Parametri za LAStile', 
                 multiLine=False, 
                 defaultValue='-tile_size 50 -buffer 5'
                 )
            )

        self.addParameter(
            QgsProcessingParameterString(
                'proc_parameters',
                'Parametri za LASground',  
                 multiLine=False, 
                 defaultValue='-step 5 -bulge 4 -spike 0.05 -down_spike 0.05 -offset 0.05 -hyper_fine'
                 )
            )

        self.addParameter(
            QgsProcessingParameterNumber(
                'dem_resolution', 
                'Ločljivost DMV', type=QgsProcessingParameterNumber.Double, defaultValue=0.5))

        self.addParameter(
            QgsProcessingParameterNumber(
                'density_resolution', 
                'Ločljivost karte gostote talnih točk', type=QgsProcessingParameterNumber.Double, defaultValue=5))

        self.addParameter(
            QgsProcessingParameterBoolean(
                'merge_grids', 
                'Združi liste v en raster',
                 optional=True, 
                 defaultValue=True
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                'outdem', 
                'Mapa za DMV', 
                behavior=QgsProcessingParameterFile.Folder, 
                fileFilter='All files (*.*)'
                )
            )
       

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        infolder = parameters['infolder']
        pathlist = []
        count = 0
        for lazfile in Path(infolder).glob('*.laz'):
            pathlist.append(lazfile)
            feedback.pushInfo(str(lazfile))
            count =count + 1

        feedback.pushInfo(self.tr('Število listov za procesiranje: %s.' % count))
        total = 100/count

        outdem = parameters['outdem'] 
        dem_resolution = parameters['dem_resolution'] 
        proc_parameters = parameters['proc_parameters'] 
        tile_params = parameters['tile_params'] 
        density_resolution = parameters['density_resolution']
        merge_grids= ['merge_grids']


        lastile = 'C:\\LAStools\\bin\\lastile.exe'
        lasground = 'C:\\LAStools\\bin\\lasground_new.exe'
        las2dem = 'C:\\LAStools\\bin\\las2dem.exe'
        lasgrid = 'C:\\LAStools\\bin\\lasgrid.exe'
        lasinfo = 'C:\\LAStools\\bin\\lasinfo.exe'
        lasindex = 'C:\\LAStools\\bin\\lasindex.exe'
         
        sum_total_all = 0
        sum_last_all = 0
        sum_ground = 0
        list_ground_points = []

        def las_info(name, laz_path, extraparam):
            info = tempfile.mkdtemp()
            info_file = Path(info)/'info.csv'
            
            with open(str(info_file), 'w') as f:
                for las_file in Path(laz_path).glob('*.las'):           
                    f.write(str(las_file))
                    f.write('\n')       
            subprocess.run('%s -cpu64 -lof %s -otxt %s -odir %s -nv -cd -nmm -ro' %(lasinfo, info_file, extraparam, info))
            
            sum_total = 0
            sum_last = 0     
            list_nr = 0
            for info_file in Path(info).glob('*.txt'):
                list_nr = list_nr + 1             
                with open(info_file, 'r') as f:
                    for line in f:
                        strsp = line.split(':')
                        if strsp[0].rstrip() == 'point density':   
                            text = str(strsp[1].rstrip())                          
                            num = re.findall('[\d]*[.][\d]+', text)        
                            sum_total = sum_total + float(num[0])
                            sum_last = sum_last + float(num[1])      
            if list_nr > 0:       
                avg_all = round(sum_total/list_nr, 3)        
                avg_last = round(sum_last/list_nr, 3)    
                if extraparam == '':
                    feedback.pushInfo('Povprečna gostota vseh odbojev lista %s: %s /m2' % (name, avg_all))
                    feedback.pushInfo('Povprečna gostota zadnjih odbojev lista %s: %s /m2' % (name, avg_last))
                    
                else:
                    feedback.pushInfo('Povprečna gostota talnih točk lista %s: %s /m2' % (name, avg_all))    
                    list_ground_points.append('%s: %s' %(name, avg_all))    
            else:
                feedback.pushInfo('Težave s potjo?: %s' % laz_path)
            shutil.rmtree(info)
            return [avg_all, avg_last]
        
        density = tempfile.mkdtemp() 
        tmp_dem = tempfile.mkdtemp() 
        for cur, laz_file in enumerate(pathlist):  
            cur = cur + 1
            tiles = tempfile.mkdtemp()
            classified = tempfile.mkdtemp()
            grid = tempfile.mkdtemp()  
            list_density = tempfile.mkdtemp() 
            name = Path(laz_file).stem
            feedback.pushInfo(self.tr('Začenjam list %s/%s: %s.' % (cur, count, name)))
            subprocess.run('%s -i %s -append' %(lasindex, laz_file,))                                                         
            subprocess.run('%s -i %s -o "tile.las" %s -reversible -olas -odir %s' %(lastile, laz_file, tile_params, tiles))
            subprocess.run('%s -i *.las -cores 16 %s -odir %s' %(lasground, proc_parameters, classified), cwd=tiles)
            shutil.rmtree(tiles)
            avgs =las_info(name, classified,'')
            avg_ground =las_info(name, classified,'-keep_classification 2')          
       
            subprocess.run('%s -i *.las -cores 16 -step %s -use_tile_bb -odir %s -obil -keep_class 2 -extra_pass' %(las2dem, dem_resolution, grid), cwd=classified)         
            subprocess.run('%s -i *.las -keep_classification 2 -step %s  -point_density -odir %s  -o -%s.asc' %(lasgrid, density_resolution, list_density, name), cwd=classified)                                                                        
            shutil.rmtree(classified)
                   
            list_input = []
            for asc_file in Path(list_density).glob('*asc'):
                list_input.append(str(asc_file))            
            
            if density_resolution == density_resolution ** 2: 
                density_list = str(density) +  '\\' + str(name) + 'density map.tif'     
            else: 
                density_list = str(list_density) +  '\\' + str(name) + 'density map_raw.tif'    

            processing.run("gdal:merge", {
                'INPUT':list_input,
                'PCT':False,
                'SEPARATE':False,
                'NODATA_INPUT':0,
                'NODATA_OUTPUT':None,
                'OPTIONS':'',
                'EXTRA':'',
                'DATA_TYPE':5,
                'OUTPUT': density_list
                }
                )  


            if density_resolution != density_resolution ** 2:   
                multipyer = density_resolution ** 2
                density_list_raw = QgsRasterLayer(density_list, 'density_raster')   
                feedback.pushInfo(self.tr(str(density_list_raw)))
                density_list = str(density) +  '\\' + str(name) + 'density map.tif' 
                feedback.pushInfo(self.tr(str(density_list)))

                entries = []
                ras = QgsRasterCalculatorEntry()
                ras.ref = 'ras@1'
                ras.raster = density_list_raw
                ras.bandNumber = 1
                entries.append( ras )
                expression = '\'ras@1\' * %s * (\'ras@1\' != -9999)' %(multipyer)   
                calc = QgsRasterCalculator( expression, density_list , 'GTiff', density_list_raw.extent(), density_list_raw.width(), density_list_raw.height(), entries )
                calc.processCalculation()
            density_list_raw = ''
            shutil.rmtree(list_density)            
         
            if merge_grids:            
                out_tif = Path(tmp_dem)/ (name + '.tif')
             
            else:
                out_tif = Path(outdem)/ (name + '.tif')
            #feedback.pushInfo(self.tr('Začenjam list lasgrid'))
            subprocess.run('%s -i *.bil -cores 16 -o %s -step %s -merged' %(lasgrid, str(out_tif), dem_resolution), cwd=grid)
            feedback.setProgress(cur * total)
            shutil.rmtree(grid)
            sum_total_all += avgs[0]
            sum_last_all += avgs[1]
            sum_ground +=avg_ground[0]
         
        if merge_grids:
            merged_map = str(outdem) + '\\DMV '+ str(dem_resolution) + ' m.tif'
            merge_dems = []
            for tif_file in Path(tmp_dem).glob('*tif'):
                merge_dems.append(str(tif_file))
            processing.run("gdal:merge", {
            'INPUT':merge_dems,
            'PCT':False,
            'SEPARATE':False,
            'NODATA_INPUT':0,
            'NODATA_OUTPUT':None,
            'OPTIONS':'',
            'EXTRA':'',
            'DATA_TYPE':5,
            'OUTPUT': merged_map
            }
            ) 
            shutil.rmtree(tmp_dem)

        merge_input = []
        for tif_file in Path(density).glob('*tif'):
            merge_input.append(str(tif_file))
            
        density_map_saga = str(density) + '\\density map.sdat'
        density_map = str(outdem) + '\\density map.tif'
      
        if len(merge_input) > 1:
            dens = processing.run("saga:mosaicrasterlayers", {
                'GRIDS':merge_input,
				'NAME':'Mosaic',
				'TYPE':7,
				'RESAMPLING':0,
				'OVERLAP':3,
				'BLEND_DIST':1,
				'MATCH':0,
				'TARGET_USER_XMIN TARGET_USER_XMAX TARGET_USER_YMIN TARGET_USER_YMAX':None,
				'TARGET_USER_SIZE':density_resolution,
				'TARGET_USER_FITS':1,
				'TARGET_OUT_GRID':density_map_saga})
         
			
            processing.run("gdal:translate", {
                'INPUT':density_map_saga,
				'TARGET_CRS':None,
				'NODATA':None,
				'COPY_SUBDATASETS':False,
				'OPTIONS':'',
				'EXTRA':'',
				'DATA_TYPE':0,
				'OUTPUT':density_map})  
          
        else:
            feedback.pushInfo('Samo en')
		
		
        shutil.rmtree(density)
        

        all_ = sum_total_all/count
        last = sum_last_all/count
        ground = sum_ground/count
        txt_all = 'Povprečna gostota vseh odbojev: %s /m2' % all_
        txt_last = 'Povprečna gostota zadnjih odbojev: %s /m2' % last
        txt_ground = 'Povprečna gostota talnih točk: %s /m2' % ground
        
        feedback.pushInfo(txt_all)
        feedback.pushInfo(txt_last)
        feedback.pushInfo(txt_ground)
        
        log_file = Path(outdem )/'lidar_process_log.txt'
        with open(str(log_file), 'a') as f:  
            f.write('\n') 
            f.write(str(datetime.datetime.now()))        
            f.write('\n') 
            f.write('Parametri procesiranja lasground: %s.' % proc_parameters)   
            f.write('\n')   
            f.write('Procesiranih je bilo %s listov.' % count)   
            f.write('\n')             
            f.write(str(txt_all))
            f.write('\n')      
            f.write(str(txt_last))
            f.write('\n')    
            f.write(str(txt_ground))
            f.write('\n') 
            f.write('Seznam listov: gostota talnih točk (/m2)\n')
            for i in list_ground_points:
                f.write(i)  
                f.write('\n')          
   
        return {}


