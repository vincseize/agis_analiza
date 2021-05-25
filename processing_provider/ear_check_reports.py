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

class EARCheckReports(QgsProcessingAlgorithm):
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
        return EARCheckReports()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'ear_check_reports'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Preveri poročila EAR')

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
        help_text = """To orodje preveri kateri vnosi v EAR imajo pripadajoč PDF. Izpiše se CPA id in velikost PDF-ja v bytih, če obstaja. 
        
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
        ear_reports = []
        
        for ear in ear_list.getFeatures():
            ear_id = str(ear[2])
            ear_reports.append(ear_id)

        ear_reports = list(dict.fromkeys(ear_reports))
        ear_reports.sort()
        feedback.pushInfo('cpa id, velikost (MB) - analiza, status-analiza, velikost (MB) - CPA GIS, status-CPA GIS')          


        ear_cpa_path = 'V:\\01 CPA - PODATKOVNE ZBIRKE\\03 GIS CPA\\Porocila\\'
        ear_path = 'V:\\01 CPA - Projekti\\10  ANALIZA\\EAR\\PDF\\'

        def check_path(path_ear, out_text):
            if os.path.isfile(path_ear):  
                size = Path(path_ear).stat().st_size     
                size = size / (1024*1024)
                size = str(round(size, 3))
                if float(size) < 0.01: 
                    out_text.append(size)
                    out_text.append('napaka?')
                else:                      
                    out_text.append(size) 
                    out_text.append('ok')        
            else:
                out_text.append('null')
                out_text.append('manjka pdf')
                size = 'null'
            return size

        total = 100.0 / len(ear_reports) 
        for current, ear_id in enumerate(ear_reports):
            path_ear = ear_path + ear_id + '.pdf'
            path_cpa = ear_cpa_path + ear_id + '.pdf'
            out_text = []
            out_text.append(ear_id)       
            ear_size = check_path(path_ear, out_text)     
            cpa_size = check_path(path_cpa, out_text)           
            if 'napaka?' in out_text or 'manjka pdf' in out_text:
                text = ', '.join(out_text)     
                feedback.reportError(str(text))
            elif cpa_size == 'null' and ear_size != 'null':
                out_text[4] = 'Ni posodobljeno?'
                text = ', '.join(out_text)
                feedback.pushInfo(str(text))
            elif cpa_size != ear_size:
                out_text[4] = 'Ni posodobljeno?'
                text = ', '.join(out_text)
                feedback.reportError(str(text))
            feedback.setProgress(int(current * total))
            if feedback.isCanceled():
                break  
        return {}


