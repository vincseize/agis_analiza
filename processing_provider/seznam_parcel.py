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
Seznam parcel 0.1
17.2.2020
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
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
                       QgsProcessingUtils
                       )
import processing
import psycopg2
from pathlib import Path
from .general_modules import *
import os


class SeznamParcelZnotrajObmojaRaziskave(QgsProcessingAlgorithm):

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
        return SeznamParcelZnotrajObmojaRaziskave()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'seznam_parcel_znotraj_obmocja_raziskave'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Seznam parcel znotraj območja raziskave')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return ''

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        help_text = """To orodje sprejme območje (poligon) raziskave ter pripravi nov začasni sloj, ki vsebuje vse parcele znotraj območja.

        Sloj je potrebno shraniti v arhiv projekta -> Načrti/GIS/00-0000 Seznam parcel.gpkg.
        Simbologijo sloja je potrebno prenesti na nov shranjen sloj (Desni klik na sloj, Slog, Kopiraj slog).
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
                self.INPUT,
                self.tr('Obmocje raziskave'),
                [QgsProcessing.TypeVectorPolygon]
                )
            )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Seznam parcel')
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
        source = self.parameterAsVectorLayer(
            parameters,
            self.INPUT,
            context
        )

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))


        # Popravi geometrije, območje

        fix_geom = processing.run("native:fixgeometries", {
                'INPUT': source,
                'OUTPUT': 'memory:'
            }, context=context, feedback=feedback)['OUTPUT']

        dissol = processing.run("native:dissolve", {
                'INPUT':fix_geom,
                'FIELD':[],
                'OUTPUT':'memory:'
            }, context=context, feedback=feedback)['OUTPUT']


        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        feedback.pushInfo('Geometrija popravljena, iščem parcele...')


        # Connect to an existing database
        conn_error = 'Povezava z podatkovno bazo je bila neuspešna'
        conn_success = 'Povezava z podatkovno bazo je uspela'
        vlayer = postgres_layer()
        if not vlayer.isValid():
            feedback.pushInfo(conn_error)
        else:
            feedback.pushInfo(conn_success)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Obreži
        clip = processing.run('native:clip', {
                'INPUT': vlayer,
                'OVERLAY': dissol,
                'OUTPUT': "memory:"
            }, context=context, feedback=feedback)['OUTPUT']


        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}
        feedback.pushInfo('Presek izračunan')

        # Refactor fields
        refa = processing.run('qgis:refactorfields', {
                'FIELDS_MAPPING': [
                    {'expression': '"fid"', 'length': 0, 'name': 'fid', 'precision': 0, 'type': 4},
                    {'expression': '"sifko"', 'length': 0, 'name': 'sifko', 'precision': 0, 'type': 2},
                    {'expression': '"parcela"', 'length': 10, 'name': 'parcela', 'precision': 0, 'type': 10},
                    {'expression': '"IMEKO"', 'length': 20, 'name': 'IMEKO', 'precision': 0, 'type': 10},
                    {'expression': '"Parcela in KO"', 'length': 0, 'name': 'Parcela in KO', 'precision': 0, 'type': 10},
                    {'expression': 'round($area,2)', 'length': 0, 'name': 'površina na trasi', 'precision': 0, 'type': 6},
                    {'expression': '"Lastnik"', 'length': 0, 'name': 'Lastnik', 'precision': 0, 'type': 10},
                    {'expression': '"Naslov"', 'length': 0, 'name': 'Naslov', 'precision': 0, 'type': 10},
                    {'expression': '"Dovoljenje"', 'length': 0, 'name': 'Dovoljenje', 'precision': 0, 'type': 10},
                    {'expression': '"Kontakt"', 'length': 0, 'name': 'Kontakt', 'precision': 0, 'type': 10},
                    {'expression': '"Opombe"', 'length': 0, 'name': 'Opombe', 'precision': 0, 'type': 10}],
                'INPUT': clip,
                'OUTPUT': "memory:"
            }, context=context, feedback=feedback)['OUTPUT']

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}
        feedback.pushInfo('Stolpci urejeni2')

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            refa.fields(),
            refa.wkbType(),
            refa.sourceCrs()
        )


        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / refa.featureCount() if refa.featureCount() else 0
        features = refa.getFeatures()

        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            # Add a feature in the sink
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.


        area = 0
        cnt = 0
        for f in refa.getFeatures():
            farea = f['površina na trasi']
            area = f['površina na trasi'] + area
            cnt = cnt + 1
        out_text = """
        *******

        Znotraj trase je %s parcel.
        Skupna površina trase je %s m2.

        Parcele:
        """ %(cnt, round(area,2))
        feedback.pushInfo(out_text)

        idx = refa.fields().indexOf('sifko')
        values = refa.uniqueValues(idx)
        prag = 1

        for val in values:
            parc_ls = []
            for f in refa.getFeatures():
                imeko = f['IMEKO']
                if f['površina na trasi'] > prag:
                    parc_ls.append(f['parcela'])
                else:
                    pass

            out_text_parc = """
            %s, k.o. %s - %s
            """ %(', '.join(parc_ls), imeko, val)
            feedback.pushInfo(out_text_parc)

        feedback.pushInfo('''
        Pri tem izpisu niso upoštevane parcele s površino manjšo od %s m2!!!

        *******''' % prag)
        self.dest_id=dest_id
        return {self.OUTPUT: dest_id}

    def postProcessAlgorithm(self, context, feedback):
        """
        PostProcessing Tasks to define the Symbology
        """
        output = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)
        output.loadNamedStyle(str(style_parcele))
        output.triggerRepaint()

        return {self.OUTPUT: self.dest_id}
