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
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingMultiStepFeedback,
                       QgsRasterLayer,
                       QgsVectorLayer,
                       QgsFeatureRequest,
                       QgsField,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterDefinition,
                       QgsGeometry,
                       QgsFeature,
                       QgsProcessingParameterField,
                       QgsProcessingParameterString,
                       QgsRasterBandStats
                       )
from qgis import processing
from pathlib import Path
import requests

class DownloadLidar(QgsProcessingAlgorithm):
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
        return DownloadLidar()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'download_lidar'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Prenesi lidar')

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
        help_text = """To orodje sloj z ZLS listi in prenese izbrane liste.
        
        Vgrajena je varovalka, da ni mogoče prenesti več kot 1000 listov lidarja zato je nujno izbrati "selected only"!
        
        """
        return self.tr(help_text)

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'zls_listi', 
                self.tr('ZLS listi'), 
                types=[QgsProcessing.TypeVectorPolygon], 
                defaultValue='ZLS_listi'
                )
            )


        fids = QgsProcessingParameterField('list', self.tr('list'), optional=False, type=QgsProcessingParameterField.Any, parentLayerParameterName='zls_listi', allowMultiple=False, defaultValue=self.tr('list'))
        fids.setFlags(fids.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(fids)

        self.addParameter(
            QgsProcessingParameterFile(
                'laz_out', 
                self.tr('Ciljna maza za .laz'), 
                behavior=QgsProcessingParameterFile.Folder, 
                fileFilter='All files (*.*)'
                )
            )
 
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).


    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
  
        field_list = parameters['list']
  
        zls_list = processing.run("native:dropgeometries", {
                'INPUT': parameters['zls_listi'],
                'OUTPUT': 'memory:'
            }, context=context)['OUTPUT']
        
        total_size = 0
        areas = [11, 12, 13, 14, 15, 16, 21, 22, 23, 24, 25, 26, 31, 32, 33, 34, 35, 36, 37]
        transffered = 0
        def get_lenght(areas, grid):
            for b in areas:
                url = 'http://gis.arso.gov.si/lidar/gkot/laz/b_%s/D96TM/TM_%s.laz' % (b, grid)
                response = requests.head(url)
                if response.status_code == 200:
                    size = int(requests.head(url).headers['content-length'])
                    return size

        def get_grid(areas, grid, dest_folder, transffered, total):
            for b in areas:
                url = 'http://gis.arso.gov.si/lidar/gkot/laz/b_%s/D96TM/TM_%s.laz' % (b, grid)
                dest_filename = dest_folder + '\\' + grid + '.laz'
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    with open(dest_filename, 'wb') as f:
                        feedback.pushDebugInfo(self.tr('Zapisujem: %s ' % dest_filename))
                        for chunk in response.iter_content(chunk_size = 5000):
                            f.write(chunk)
                            transffered = transffered + 1
                            feedback.setProgress(transffered * total)

        if zls_list.featureCount() > 1000:
            raise QgsProcessingException('Preveč listov: %s, dovoljeno je do 1000' %zls_list.featureCount())
      
        else:
            for a in zls_list.getFeatures():
                total_size = total_size + get_lenght(areas, a[field_list])

            total_chunks = total_size/5000
            total = 100/total_chunks
            size_mb = total_size/1024/1024
            feedback.pushDebugInfo(self.tr('Prenašam %s listov (%s Mb)' % (zls_list.featureCount(), round(size_mb,2))))

            
            for a in zls_list.getFeatures():
                get_grid(areas, a[field_list], parameters['laz_out'], transffered, total)
                feedback.pushDebugInfo(str(a[field_list]))
       
        return {}


