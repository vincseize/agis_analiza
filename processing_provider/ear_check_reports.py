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
                       QgsProcessingParameterMapLayer,
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
            QgsProcessingParameterMapLayer(
                'ear_raziskave', 
                self.tr('Evidenca arheoloških raziskav'), 
                types=[QgsProcessing.TypeVectorPolygon], 
                defaultValue='Evidenca arheoloških raziskav'
                )
            )
     
        self.addParameter(QgsProcessingParameterBoolean('ear_analiza', '10  ANALIZA\\EAR\\PDF', optional=True, defaultValue=True))
        self.addParameter(QgsProcessingParameterBoolean('ear_giscpa', '03 GIS CPA\\Porocila', optional=True, defaultValue=False))

 
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

        layer = QgsProject.instance().mapLayer(parameters['ear_raziskave'])
        layer.startEditing()
        def check_everything(layer, ear_path, field):
            for feature in layer.getFeatures():
                fields = layer.fields()
                field_id = fields.indexFromName(field)
                ear_id = str(feature[2])
                path = ear_path + ear_id + '.pdf'
                if os.path.isfile(path):  
                    size = Path(path).stat().st_size     
                    size = size / (1024*1024)
                    size = round(size, 3)
                    if size < 0.1: 
                        feedback.reportError('%s; %s MB; Poročilo je pokvarjeno?' % (ear_id, str(size)), False)
                    else:
                        feedback.pushInfo(self.tr('%s; %s MB; Poročilo je ok.' % (ear_id, str(size))))                  
                else:
                    feedback.reportError('%s; NULL; Poročilo ne obstaja!' % (ear_id), False)

        if parameters['ear_giscpa']:
            ear_path = 'V:\\01 CPA - PODATKOVNE ZBIRKE\\03 GIS CPA\\Porocila\\'
            field_cpa = QgsField( 'gis cpa pdf', QVariant.Double )
            layer.addExpressionField( ' NULL ', field_cpa )
            feedback.pushInfo(self.tr('Preverjam %s.' % ear_path))
            check_everything(layer, ear_path, 'gis cpa pdf')

        if parameters['ear_analiza']:
            ear_path = 'V:\\01 CPA - Projekti\\10  ANALIZA\\EAR\\PDF\\'
            field_analiza = QgsField( 'analiza pdf', QVariant.Double )
            layer.addExpressionField( ' NULL ', field_analiza )
            feedback.pushInfo(self.tr('Preverjam %s.' % ear_path))
            check_everything(layer, ear_path, 'analiza pdf')
         
        return {}


