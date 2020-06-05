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
                       QgsFeatureSource
                                         
                       )
import processing
import psycopg2
from pathlib import Path
from ..general_modules import (path,
                               wfs_layer,
                               access,
                               postgis_connect
                        )


import os



class SeznamParcelZnotrajObmojaRaziskave(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    BUFFER_INPUT = 'BUFFER_INPUT'
    THRES_INPUT = 'THRES_INPUT'

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
        help_text = """To orodje sprejme območje raziskave ter pripravi nov začasni sloj, ki vsebuje vse parcele znotraj območja. 
        Vir podatka parcel je zemljiškokatasterski načrt naložen v podatkovni bazi CPA ali po izbiri zemljiškokatasterski prikaz, dostopen preko spletne stritve INSPIRE.
        V primeru linij ali točk je obvezna vrednost bufferja (polovična razdalja širine posega). 

        Po potrebi, se predhodno uporabi orodje "intersect" za izrez območij znotraj EŠD.
        
        Sloj shranimo v arhiv projekta -> Načrti/GIS/00-0000 Seznam parcel.gpkg.
        
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
            QgsProcessingParameterBoolean(
                'use_zkp', 
                'Uporabi zemljiškokatastrski prikaz namesto načrta (Meje ZK so lahko nepravilne!).',
                 optional=True, 
                 defaultValue=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'obmocje',
                self.tr('Obmocje raziskave'),
                types=[QgsProcessing.TypeVectorAnyGeometry]
                )
            )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.BUFFER_INPUT,
                self.tr('Buffer'),
                True,
                [QgsProcessingParameterNumber.Double],
                2
                )
            )

        self.addParameter(
            QgsProcessingParameterNumber(  
                self.THRES_INPUT,
                self.tr('Prag velikosti za izključitev parcel iz izpisa (m2)'),
                optional = False,
                type=QgsProcessingParameterNumber.Double, 
                defaultValue=0.5
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
        source = self.parameterAsSource(
            parameters,
            'obmocje',
            context
        )
        buffer_value = parameters[self.BUFFER_INPUT]
        
        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
               
        # Fix geometry
        fix_geom = processing.run("native:fixgeometries", {
                'INPUT': parameters['obmocje'],
                'OUTPUT': 'memory:'
            }, context=context)['OUTPUT']
        
        if str(fix_geom.geometryType()) != '2' and buffer_value == 0.0:
            raise QgsProcessingException("Buffer value should not be 0 when not using polygon layers!")
              


        feedback.pushInfo(self.tr('Geometry fixed.'))
        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Dissolve
        dissol = processing.run("native:dissolve", {
                'INPUT':fix_geom,
                'FIELD':[],
                'OUTPUT':'memory:'
            }, context=context)['OUTPUT']

        feedback.pushInfo(self.tr('Dissolved.'))
        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        #Apply buffer and Reproject layer

        if str(fix_geom.geometryType()) == '0':
            cap_style = 2
        else:
            cap_style = 1

        buffer = processing.run("native:buffer", {
            'DISSOLVE': False,
            'DISTANCE': buffer_value,
            'END_CAP_STYLE': cap_style,
            'INPUT': dissol,
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 10,
            'OUTPUT':'memory:'
        }, context=context)['OUTPUT']
        reprojected = processing.run("native:reprojectlayer", {
                'INPUT':buffer,
                'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:3794'),
                'OUTPUT':'memory:'
            }, context=context)['OUTPUT']
        feedback.pushInfo(self.tr('%s m buffer applied, layer reprojected to EPSG:3794' % buffer_value))
        

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        extent = reprojected.extent()
        xmin=extent.xMinimum()
        xmax=extent.xMaximum()
        ymin=extent.yMinimum()
        ymax=extent.yMaximum()
        extent = '%s %s, %s %s, %s %s, %s %s, %s %s' %(xmin, ymin, xmax, ymin, xmax, ymax, xmin, ymax, xmin, ymin)



        if parameters['use_zkp']:
            # Connect to an INSPIRE Cadaster
            parcels_sql = "SELECT * FROM CadastralParcel where ST_Intersects(geometry, ST_GeometryFromText(\'POLYGON(("   +  extent  +  "))\', 3794))"
            parc_layer = wfs_layer(self, 'Parcele', 'cp:CadastralParcel', 'EPSG:3794', 'https://storitve.eprostor.gov.si/ows-ins-wfs/cp/ows', parcels_sql)
        
        else:
            # Connect to database Cadaster
            if access(self):
                parc_layer = postgis_connect(self, 'public', 'ZKN parcele', 'geom', 'fid')
            else:
                feedback.reportError(self.tr('Ni povezave s CPA podatkovno bazo!'))


        ko_sql = "SELECT * FROM KO_G where ST_Intersects(KO_G.GEOMETRY, ST_GeometryFromText(\'POLYGON(("   +  extent  +  "))\', 3794))" 
        ko_layer = wfs_layer(self, 'Ko', 'SI.GURS.ZK:KO_G', 'EPSG:3794', 'https://storitve.eprostor.gov.si/ows-pub-wfs/ows', ko_sql)

       
        if parc_layer.isValid() and ko_layer.isValid():
            feedback.pushInfo(self.tr('Success accessing Cadaster'))
        elif parc_layer.isValid() and not ko_layer.isValid():
            feedback.pushDebugInfo(self.tr("Error, can not access K. O. layer: https://storitve.eprostor.gov.si/ows-pub-wfs/ows"))
        elif not parc_layer.isValid() and ko_layer.isValid():
            feedback.pushDebugInfo(self.tr("Error, can not access Parcels"))
        else:
            feedback.pushDebugInfo(self.tr("Error, can not access Cadaster"))

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}


        # Clip
        clip = processing.run('native:clip', {
                'INPUT': parc_layer,
                'OVERLAY': reprojected,
                'OUTPUT': 'memory:'
            }, context=context)['OUTPUT']
        
 
        feedback.pushInfo(self.tr('Cadaster cliped'))
 
        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        #Join cadastral names
        if parameters['use_zkp']:
            clip = processing.run('qgis:refactorfields', {
                    'FIELDS_MAPPING': [
                        {'expression': "regexp_substr(nationalCadastralReference,'(\\\\d+)')", 'length': 0, 'name': 'SIFKO', 'precision': 0, 'type': 2},
                        {'expression': '"label"', 'length': 0, 'name': 'parcela', 'precision': 0, 'type': 10}], 
                    'INPUT': clip,
                    'OUTPUT': "memory:"
                }, context=context, )['OUTPUT']

        else:
            clip = processing.run('qgis:refactorfields', {
                    'FIELDS_MAPPING': [
                        {'expression': "sifko", 'length': 0, 'name': 'SIFKO', 'precision': 0, 'type': 2},
                        {'expression': 'parcela', 'length': 0, 'name': 'parcela', 'precision': 0, 'type': 10},
                        {'expression': '"Vrsta parcele"', 'length': 0, 'name': 'Vrsta parcele', 'precision': 0, 'type': 10},], 
                    'INPUT': clip,
                    'OUTPUT': "memory:"
                }, context=context, )['OUTPUT']




        ko = processing.run('qgis:refactorfields', {
                'FIELDS_MAPPING': [
                    {'expression': "SIFKO", 'length': 0, 'name': 'SIFKO', 'precision': 0, 'type': 2},
                    {'expression': '"IMEKO"', 'length': 0, 'name': 'IMEKO', 'precision': 0, 'type': 10}], 
                'INPUT': ko_layer,
                'OUTPUT': "memory:"
            }, context=context, )['OUTPUT']


        shpField = 'SIFKO'
        csvField = 'SIFKO'
        joinObject = QgsVectorLayerJoinInfo()
        joinObject.setJoinFieldName(csvField)
        joinObject.setTargetFieldName(shpField)
        joinObject.setJoinLayerId(ko.id())
        joinObject.setUsingMemoryCache(True)
        joinObject.setJoinLayer(ko)
        clip.addJoin(joinObject)

        feedback.pushInfo(self.tr('Cadaster joined'))

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        
        # Refactor fields
        refa = processing.run('qgis:refactorfields', {
                'FIELDS_MAPPING': [
                    {'expression': '@row_number', 'length': 0, 'name': 'fid', 'precision': 0, 'type': 2},
                    {'expression': '"sifko"', 'length': 0, 'name': 'sifko', 'precision': 0, 'type': 2},
                    {'expression': '"parcela"', 'length': 0, 'name': 'parcela', 'precision': 0, 'type': 10}, 
                    {'expression':  '"output_IMEKO"', 'length': 20, 'name': 'IMEKO', 'precision': 0, 'type': 10},
                    {'expression': 'round($area,2)', 'length': 0, 'name': 'površina na trasi', 'precision': 0, 'type': 6},
                    {'expression': '"Lastnik"', 'length': 0, 'name': 'Lastnik', 'precision': 0, 'type': 10},
                    {'expression': '"Naslov"', 'length': 0, 'name': 'Naslov', 'precision': 0, 'type': 10},
                    {'expression': '"Dovoljenje"', 'length': 0, 'name': 'Dovoljenje', 'precision': 0, 'type': 10},
                    {'expression': '"Kontakt"', 'length': 0, 'name': 'Kontakt', 'precision': 0, 'type': 10},
                    {'expression': '"Vrsta parcele"', 'length': 0, 'name': 'Vrsta parcele', 'precision': 0, 'type': 10},
                    {'expression': '"Opombe"', 'length': 0, 'name': 'Opombe', 'precision': 0, 'type': 10}],
                'INPUT': clip,
                'OUTPUT': "memory:"
            }, context=context, )['OUTPUT']


        feedback.pushInfo(self.tr('Fields refactored'))
        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

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


        #Check size matching
        in_area = 0
        out_area = 0
        if str(fix_geom.geometryType()) != '2':
            for feature in buffer.getFeatures():
                in_area = in_area + feature.geometry().area()
        else:
            for feature in dissol.getFeatures():
                in_area = in_area + feature.geometry().area()

        for feature in refa.getFeatures():
            out_area = out_area + feature.geometry().area()

        #Output summary
        area = 0
        cnt = 0
        for f in refa.getFeatures():
            farea = f['površina na trasi']
            area = f['površina na trasi'] + area
            cnt = cnt + 1
        out_text = self.tr("""
        *******

        Znotraj trase je %s parcel.
        Skupna površina trase je %s m2.

        Parcele:
        """) %(cnt, round(area,2))
        feedback.pushInfo(out_text)

        idx = refa.fields().indexOf('sifko')
        values = refa.uniqueValues(idx)
        #Set treshold to not include parcel 
        prag = parameters[self.THRES_INPUT]

        for val in values:
            parc_ls = []
            for f in refa.getFeatures():  
                sifko = f['sifko']
                if f['površina na trasi'] > prag and sifko == val:
                    parc_ls.append(f['parcela'])
                    imeko = f['IMEKO']
                else:
                    pass
            out_text_parc = """
            %s, k.o. %s - %s
            """ %(', '.join(parc_ls), str(imeko), val)
            feedback.pushInfo(out_text_parc)
        
        feedback.pushInfo('''
        Pri tem izpisu niso upoštevane parcele s površino manjšo od %s m2!!!
        ''' % prag)

        if parameters['use_zkp']:
            feedback.reportError('''Pri izračunu je bil uporabljen zemljiškokatastrski prikaz, ne načrt!
            Podrobnosti o razliki so na voljo na naslovu: 
            https://www.e-prostor.gov.si/fileadmin/struktura/Opis_strukture_graficnih_podatkov_ZK.pdf
            
             ''')

        else:
            if round(out_area, 2) != round(in_area, 2):
                feedback.reportError('''Površina rezultata (%s m2) se ne ujema z vhodnim slojem (%s m2). Verjetno ZKN na območju raziskav ni zvezen!
                Več o viru podatka ZKN: 
                https://www.e-prostor.gov.si/fileadmin/struktura/Opis_strukture_graficnih_podatkov_ZK.pdf  
                
                ''' %(round(out_area,2), round(in_area,2)))
        

        if parameters['use_zkp'] is not True:
            feedback.pushDebugInfo('Pri izračunu je bil uporabljen %s. ' % parc_layer.dataComment())
            
        feedback.pushInfo('''

        *******''')

        self.dest_id=dest_id
        return {self.OUTPUT: dest_id}

    def postProcessAlgorithm(self, context, feedback):
        """
        PostProcessing Tasks to define the Symbology
        """
        output = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)
        style_parcele = path('styles')/'Seznam parcel_dovoljenja.qml'
        output.loadNamedStyle(str(style_parcele))
        output.triggerRepaint()

        return {self.OUTPUT: self.dest_id}
