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
import shutil
import os

class EARDownloadReports(QgsProcessingAlgorithm):
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
        return EARDownloadReports()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'ear_download_reports'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Kopiraj poročila iz EAR')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('majadb vzdrževanje')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'db_updates'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        help_text = """To orodje prenese PDF-je poročil izbranih raziskav iz Evidence arheoloških raziskav.
        
        Vgrajena je varovalka, da ni mogoče hkrati prenesti več kot 500 poročil, zato je nujno izbrati "selected only"!
        
        """
        return self.tr(help_text)

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'ear_raziskave', 
                self.tr('Evidenca arheoloških raziskav'), 
                types=[QgsProcessing.TypeVectorPolygon], 
                defaultValue='Evidenca arheoloških raziskav'
                )
            )

        self.addParameter(
            QgsProcessingParameterFile(
                'pdf_out', 
                self.tr('Ciljna mapa za poročila'), 
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
  
        ear_list = processing.run("native:dropgeometries", {
                'INPUT': parameters['ear_raziskave'],
                'OUTPUT': 'memory:'
            }, context=context)['OUTPUT']

        total_nr = ear_list.featureCount()
        total_size = 0

        feedback.pushInfo(self.tr('Izbranih je %s raziskav.' % total_nr))

        if  total_nr > 500:
            raise QgsProcessingException('Preveč raziskav: %s, dovoljeno je do 500!' %total_nr)
        else:
            feedback.pushInfo(self.tr('Kopiram poročila: ' ))

        ear_path = 'V:\\01 CPA - Projekti\\10  ANALIZA\\EAR\\PDF\\'
        ear_dest = parameters['pdf_out'] + '\\'
        ear_reports = []
      

        for ear in ear_list.getFeatures():
            ear_id = str(ear[2])
            path = ear_path + ear_id + '.pdf'
            destination = ear_dest  + ear_id + '.pdf'
            
            if os.path.isfile(destination) and os.path.isfile(path):
                dest_size = Path(destination).stat().st_size
                size = Path(path).stat().st_size
                if dest_size == size:
                    feedback.pushDebugInfo(self.tr('%s že obstaja v ciljni mapi.' %  str(ear_id)))
                else:
                    ear_reports.append(ear_id)
                    total_size += size
            elif os.path.isfile(path):
                size = Path(path).stat().st_size
                ear_reports.append(ear_id)
                total_size += size     
            else:
                feedback.reportError(self.tr('PDF %s ne obstaja?!' % str(ear_id)))

        total_nr = len(ear_reports)
        feedback.pushInfo(self.tr('Kopiram %s poročil v velikosti %s MB' % (str(total_nr), str(round((total_size/1024/1024),2)))))
        transffered = 0
        total_chunks = total_size/5000 if total_size> 0 else 1
        total = 100/(total_size/1024/1024)
        

        def name(id_porocila, ear_path, ear_dest, total):
            out_pdf =  ear_path + str(id_porocila) + '.pdf'
            destination = ear_dest + str(id_porocila) + '.pdf'
            feedback.pushDebugInfo(self.tr('Kopiram %s.' % id_porocila))
            feedback.pushDebugInfo(self.tr('Kopiram %s.' % destination))
            feedback.pushDebugInfo(self.tr('Kopiram %s.' % out_pdf))
            shutil.copy(out_pdf, destination)
            size = Path(destination).stat().st_size
            curr_size = size/1024/1024
            feedback.setProgress( curr_size * total)

        for current, i in enumerate(ear_reports):
            name(i, ear_path, ear_dest, total)

        feedback.pushInfo(self.tr('Konec'))
       
        """
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
       """
        return {}


