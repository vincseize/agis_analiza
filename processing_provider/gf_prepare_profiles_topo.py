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

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (Qgis,
                       QgsFeatureRequest,
                       QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFile,
                       QgsVectorLayer,
                       QgsProcessingMultiStepFeedback,
                       QgsApplication,
                       QgsProject,
                       QgsProcessingUtils,
                       QgsProcessingParameterNumber,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterVectorLayer                           
                       )
import processing
from pathlib import Path
from ..general_modules import (path,
                     
                        )



class GfPrepareProfilesTopo(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    SPACING = 'SPACING'
    RASTER = 'RASTER'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return GfPrepareProfilesTopo()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'gf_preprare_profiles_topo'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Topo podatki profilov')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Geofizika')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'geofizika'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        help_text = """
        
        """
        return self.tr(help_text)

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.


        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'profiles',
                self.tr('GPR profili'),
                types=[QgsProcessing.TypeVectorLine]
                )
            )

 
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.RASTER, 
                self.tr('DMV'), 
                defaultValue=None
                )
            )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.SPACING,
                self.tr('Gostota točk'),
                optional = False,
                type=QgsProcessingParameterNumber.Double, 
                defaultValue=0.5
                )
            )


        try:
            default_out_file = Path(QgsProject.instance().homePath()).parents[0]/self.tr('Geofizika/GPR/02_proc')
        except:
            default_out_file = ''


        self.addParameter(
            QgsProcessingParameterFile(
                self.OUTPUT, 
                self.tr('Ciljna mapa'), 
                behavior=QgsProcessingParameterFile.Folder,
                defaultValue=str(default_out_file)
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        feedback = QgsProcessingMultiStepFeedback(5, feedback)

        results = {}
        outputs = {}

        source = self.parameterAsLayer(
            parameters,
            'profiles',
            context
            )
        spacing = parameters[self.SPACING]
        out_folder = parameters[self.OUTPUT]

        # Split lines by maximum length
        split = processing.run('native:pointsalonglines', {
            'INPUT': source,
            'DISTANCE': spacing,
            'START_OFFSET':0,
            'END_OFFSET':0,
            'OUTPUT': "memory:"
            }, context=context)['OUTPUT']


        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}


        # Drape (set Z value from raster)
        draped = processing.run('native:setzfromraster', {
            'BAND': 1,
            'INPUT': split,
            'NODATA': 0,
            'RASTER': parameters[self.RASTER],
            'SCALE': 1,
            'OUTPUT': "memory:"
            }, context=context)['OUTPUT']
      
        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Refactor fields
        refa = processing.run('qgis:refactorfields', {
                'FIELDS_MAPPING':[
                    {'expression': '"pr_name"', 'length': 0, 'name': 'pr_name', 'precision': 0, 'type': 10},
                    {'expression': '"kv"', 'length': 0, 'name': 'kv', 'precision': 0, 'type': 2},
                    {'expression': '"pr_id"', 'length': 0, 'name': 'pr_id', 'precision': 0, 'type': 2}, 
                    {'expression': '"path"', 'length': 200, 'name': 'path', 'precision': 0, 'type': 10}, 
                    {'expression': '$x', 'length': 0, 'name': 'x', 'precision': 0, 'type': 6}, 
                    {'expression': '$y', 'length': 0, 'name': 'y', 'precision': 0, 'type': 6}, 
                    {'expression': ' z( $geometry)', 'length': 0, 'name': 'z', 'precision': 0, 'type': 6},
                    {'expression': '"distance"', 'length': 0, 'name': 'z', 'precision': 0, 'type': 6}],
                    'INPUT': draped,
                     'OUTPUT': "memory:"
                }, context=context, )['OUTPUT']

       

        folder = out_folder + '\\Topo'
        Path(folder).mkdir(parents=True, exist_ok=True)
        #Get unique profiles
        idxp = refa.fields().indexOf('pr_name')
        profiles = refa.uniqueValues(idxp)
        for profile in profiles:
            topo_file = folder + '\\' + str(profile) + '.txt'
            feedback.pushInfo(self.tr('Pripravljam topo podatke za profil: %s' %profile))
            with open(topo_file, 'w') as p:
                flist = []
                request = QgsFeatureRequest()
                clause = QgsFeatureRequest.OrderByClause('distance', ascending=True)
                orderby = QgsFeatureRequest.OrderBy([clause])
                QgsFeatureRequest().setOrderBy(orderby)
                features = refa.getFeatures(request)
                for feature in features:
                    if feature[0]  == profile:
                        line = '%s, %s, %s' %(feature[4],feature[5],feature[6]) 
                        p.write(line)
                        p.write('\n')
            
      

        return {}
