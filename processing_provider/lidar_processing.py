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

from qgis.core import (QgsProject,
                       QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,      
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFile,               
                       QgsProcessingMultiStepFeedback,
                       QgsRasterLayer,                     
                       QgsProcessingParameterString,
                       QgsProcessingParameterNumber
                       )
from qgis import processing
from pathlib import Path
import tempfile
import subprocess
import shutil
import re


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
                 fileFilter='All files (*.*)', 
                 defaultValue='E:\\DPNJI\\Hrastnik\\test1'
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
            QgsProcessingParameterFile(
                'outdem', 
                'Mapa za DMV', 
                behavior=QgsProcessingParameterFile.Folder, 
                fileFilter='All files (*.*)', 
                defaultValue='E:\\DPNJI\\out'
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
            count =count + 1

        feedback.pushInfo(self.tr('Število listov za procesiranje: %s.' % count))
        total = 100/count

        outdem = parameters['outdem'] 
        dem_resolution = parameters['dem_resolution'] 
        proc_parameters = parameters['proc_parameters'] 
        tile_params = parameters['tile_params'] 

        lastile = 'C:\\LAStools\\bin\\lastile.exe'
        lasground = 'C:\\LAStools\\bin\\lasground_new.exe'
        las2dem = 'C:\\LAStools\\bin\\las2dem.exe'
        lasgrid = 'C:\\LAStools\\bin\\lasgrid.exe'
        lasinfo = 'C:\\LAStools\\bin\\lasinfo.exe'


        def las_info(name, laz_path):
            info = tempfile.mkdtemp()
            info_file = Path(info)/'info.csv'
            with open(str(info_file), 'w') as f:
                for las_file in Path(laz_path).glob('*.las'):
                    f.write(str(las_file))
                    f.write('\n')       
            subprocess.run('%s -cpu64 -lof %s -otxt -odir %s -nv -cd -nmm -ro' %(lasinfo, info_file, info))

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
                feedback.pushInfo('Povprečna gostota vseh odbojev: %s' % avg_all)
                feedback.pushInfo('Povprečna gostota zadnjih odbojev: %s' % avg_last)
            else:
                feedback.pushInfo('Ni info?!')
            shutil.rmtree(info)
        
        
        
        for cur, laz_file in enumerate(pathlist):  
            tiles = tempfile.mkdtemp()
            classified = tempfile.mkdtemp()
            grid = tempfile.mkdtemp()
            name = Path(laz_file).stem
            feedback.pushInfo(self.tr('Začenjam list %s.' % name))
            subprocess.run('%s -i %s -o "tile.las" %s -flag_as_withheld -reversible -extra_pass -olas -odir %s' %(lastile, laz_file, tile_params, tiles))
            subprocess.run('%s -i *.las -cores 16 %s -odir %s' %(lasground, proc_parameters, classified), cwd=tiles)
            shutil.rmtree(tiles)
            las_info(name, classified)
            subprocess.run('%s -i *.las -cores 16 -step %s -use_tile_bb -odir %s -obil -keep_class 2 -extra_pass' %(las2dem, dem_resolution, grid), cwd=classified)
            shutil.rmtree(classified)
            out_tif = Path(outdem)/ (name + '.tif')
            subprocess.run('%s -i *.bil -cores 16 -o %s -step %s -merged' %(lasgrid, str(out_tif), dem_resolution), cwd=grid)
            feedback.setProgress(cur * total)
            shutil.rmtree(grid)
        
        
        return {}


