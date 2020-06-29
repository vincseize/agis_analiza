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
                       QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsDataSourceUri,
                       QgsVectorLayer,
                       QgsProcessingMultiStepFeedback,
                       QgsApplication,
                       QgsProject,
                       QgsProcessingUtils,
                       QgsProcessingParameterNumber,
                       QgsCoordinateReferenceSystem,
                       QgsVectorLayerJoinInfo,
                       QgsProcessingParameterBoolean,
                       QgsFeatureSource,
                       QgsProcessingParameterFile
                                         
                       )
import processing
import xlwt
from pathlib import Path
from ..general_modules import (path,
                        )


import os



class DopisiLastnikom(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DopisiLastnikom()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'dopisi_lastnikom'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Pripravi dopise za lastnike')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Priprava projektov')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'priprava_projektov'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        help_text = """To orodje sprejme seznam parcel s podatki o lastnikih in pripravi Excel datoteko z združenimi parcelami po lastnikih.
        
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
                'parcele',
                self.tr('Seznam parcel z lastniki'),
                types=[QgsProcessing.TypeVectorAnyGeometry]
                )
            )

        try:
            default_out_file = Path(QgsProject.instance().homePath()).parents[0]/self.tr('Dokumentacija/Lastniki.xls')
        except:
            default_out_file = ''

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFile(
                self.OUTPUT,
                self.tr('Dopisi'),
                behavior=QgsProcessingParameterFile.File, 
                fileFilter='All Files (*.*)', 
                defaultValue=str(default_out_file)
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        feedback = QgsProcessingMultiStepFeedback(10, feedback)

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(
            parameters,
            'parcele',
            context
        )     

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
      
        def fke_emso(lastnik, naslov):
            fke_emso = hash(str(lastnik).replace(" ", "") + str(naslov).replace(" ", ""))
            return fke_emso  
        def field_index(layer, field):
            field_index = layer.fields().indexOf(field)
            return field_index    

        refa = processing.run('qgis:refactorfields', {
                'FIELDS_MAPPING':[
                    {'expression': '"fid"', 'length': 0, 'name': 'fid', 'precision': 0, 'type': 4}, 
                    {'expression': '"sifko"', 'length': 0, 'name': 'sifko', 'precision': 0, 'type': 2}, 
                    {'expression': '"parcela"', 'length': 0, 'name': 'parcela', 'precision': 0, 'type': 10}, 
                    {'expression': '"IMEKO"', 'length': 20, 'name': 'IMEKO', 'precision': 0, 'type': 10}, 
                    {'expression': '"Lastnik"', 'length': 0, 'name': 'Lastnik', 'precision': 0, 'type': 10}, 
                    {'expression': '"Naslov"', 'length': 0, 'name': 'Naslov', 'precision': 0, 'type': 10},
                    {'expression': '""', 'length': 0, 'name': 'uni_id', 'precision': 0, 'type': 2}],
                    'INPUT': parameters['parcele'],
                    'OUTPUT': "memory:"
            }, context=context, feedback=feedback)['OUTPUT']


        refa.startEditing()
        for feature in refa.getFeatures():
            refa.changeAttributeValue(feature.id(), field_index(refa, 'uni_id'), fke_emso(feature[4], feature[5]))
        refa.commitChanges()

        wb = xlwt.Workbook()
        ws = wb.add_sheet('Lastniki')
        ws.write(0, 0, 'Lastnik')
        ws.write(0, 1, 'Naslov')
        ws.write(0, 2, 'parcela in K.O.')

        lastniki = refa.uniqueValues(field_index(refa,'uni_id'))
        ko = refa.uniqueValues(field_index(refa,'sifko'))
        for index, uni_id in enumerate(lastniki):  
            for obcina in ko:
                parcele = refa.getFeatures('\"sifko\" = %s and \"uni_id\" = %s' %(obcina, uni_id))
                kvantifikator = "k.o. "
                cnt=0
                szn_parc = []
                for parcela in parcele:
                    cnt = cnt + 1
                    szn_parc.append(parcela[2])
                    ime_ko = parcela[3]
                    lastnik = parcela[4]
                    naslov = parcela[5]
                if cnt == 2:
                    kvantifikator = "obe k.o. "
                if cnt > 2:
                    kvantifikator = "vse k.o. "
                    
                #feedback.pushInfo(str(ime_ko))
                parcele_ko = str(', '.join(szn_parc)) + " " + kvantifikator + ime_ko + " (" + str(obcina) + "); "
                lastnik_dopis = lastnik
                lastnik_naslov = naslov
            ws.write(index + 1, 0, str(lastnik_dopis))
            ws.write(index + 1, 1, str(lastnik_naslov))
            ws.write(index + 1, 2, str(parcele_ko))
  
        out_path = str(parameters[self.OUTPUT])
        wb.save(out_path)    
        feedback.pushInfo('Shranjeno v: %s' % out_path)

        return {}

