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
Update ZKN
13.5.2020
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
                       QgsProcessingParameterString,
                       QgsProcessingParameterField,
                       QgsProcessingParameterDefinition
                     
                    
                       )
import processing
import psycopg2
from pathlib import Path
from ..general_modules import (path,
                               wfs_layer
                        )


import os



class UpdateZkn(QgsProcessingAlgorithm):

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
        return UpdateZkn()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'update_zkn'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Posodobi ZKN parcele')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Posodobitve majadb')

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
        help_text = """To orodje sprejme ZKN ter posodobi potatek v podatkovni bazi.
        
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
                self.tr('ZK_SLO_ZKN_PRCL'), 
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        
        try:
            default_user = os.getlogin()
        except:
            default_user = ''

        self.addParameter(
            QgsProcessingParameterString(
                'uporabnik', 
                'uporabnik', 
                multiLine=False, 
                defaultValue=default_user
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                'geslo', 
                'geslo', 
                multiLine=False, 
                defaultValue='oza31'
            )
        )
        
        param = QgsProcessingParameterField('sys', 'SYS_ODDTM', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, defaultValue='SYS_ODDTM')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('parcela', 'PARCELA', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, defaultValue='PARCELA')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('sifko', 'SIFKO', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, defaultValue='SIFKO')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('rang', 'RANG', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, defaultValue='RANG')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('vrstap', 'VRSTAP', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, defaultValue='VRSTAP')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        
        

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        feedback = QgsProcessingMultiStepFeedback(10, feedback)

        user = parameters['uporabnik']
        password = parameters['geslo']
        
        
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
   
        if source.featureCount() < 3000000:
            #raise QgsProcessingException("Majhno število parcel: %s, preveri vhodni sloj!!" % source.featureCount())
            feedback.reportError("Majhno število parcel: %s, preveri vhodni sloj!!" % source.featureCount())


        self.host = "majadb"
        self.database = "CPA_Analiza"
        self.user = "matjaz.mori"
        self.password = password
        self.port = "5432"
        connection = psycopg2.connect(
            host=self.host,
            port=self.port, 
            database=self.database, 
            user=self.user, 
            password=self.password, 
            connect_timeout=1 
        )     
        
        cursor = connection.cursor()
        sql = "TRUNCATE \"Delovno\".\"zkn parcele\""
        cursor.execute(sql)
        
        connection.commit()



        self.host = "majadb"
        self.database = "CPA_Analiza"
        self.user = "matjaz.mori"
        self.password = password
        self.port = "5432"
        connection = psycopg2.connect(
            host=self.host,
            port=self.port, 
            database=self.database, 
            user=self.user, 
            password=self.password, 
            connect_timeout=1 
        )          
        cursor = connection.cursor()
        sql = "TRUNCATE \"Delovno\".\"zkn parcele\""
        cursor.execute(sql)

        for feature in source.getFeatures():
            sifko = feature[parameters['sifko']]
            parcela = feature[parameters['paracela']]
            stev = 
            podd = 
            vrstap = 
            rang = 
            sys_oddtm = 
            geom = 
            feedback.reportError(str(pc_mid))


           #cursor.execute("INSERT INTO \"Delovno\".\"zkn parcele\" (pc_mid, sifko, parcela, parcela, stev, podd, vrstap, rang, sys_oddtm, geom) VALUES (" + '\'' + row[0] + '\'' + ", " + str(row[1]) + ", " + str(row[2]) + ", " + str(row[3]) + ", " + str(row[4]) + ", " + str(row[5]) + ", " + str(row[6]) + ", " + str(row[7]) + ", " + str(id) + ", ST_GeometryFromText(" + "'" + wkt + "', 32616))")



        """uri = "dbname='test' host=localhost port=5432 user='user' password='password' key=gid type=POINT table=\"public\".\"test\" (geom) sql="
        crs = None
        # layer - QGIS vector layer
        error = QgsVectorLayerImport.importLayer(layer, uri, "postgres", crs, False, False)
        if error[0] != 0:
            iface.messageBar().pushMessage(u'Error', error[1], QgsMessageBar.CRITICAL, 5)
        """   





        """        
        # Fix geometry
        fix_geom = processing.run("native:fixgeometries", {
                'INPUT': source,
                'OUTPUT': 'memory:'
            }, context=context)['OUTPUT']
        
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
     
        if str(source.geometryType()) == '0':
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

        # Connect to an INSPIRE Cadaster
        parcels_sql = "SELECT * FROM CadastralParcel where ST_Intersects(geometry, ST_GeometryFromText(\'POLYGON(("   +  extent  +  "))\', 3794))"
        parc_layer = wfs_layer(self, 'Parcele', 'cp:CadastralParcel', 'EPSG:3794', 'https://storitve.eprostor.gov.si/ows-ins-wfs/cp/ows', parcels_sql)
        
      
        ko_sql = "SELECT * FROM KO_G where ST_Intersects(KO_G.GEOMETRY, ST_GeometryFromText(\'POLYGON(("   +  extent  +  "))\', 3794))" 
        ko_layer = wfs_layer(self, 'Ko', 'SI.GURS.ZK:KO_G', 'EPSG:3794', 'https://storitve.eprostor.gov.si/ows-pub-wfs/ows', ko_sql)
      
        if parc_layer.isValid() and ko_layer.isValid():
            feedback.pushInfo(self.tr('Success accessing Cadaster'))
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
        clip = processing.run('qgis:refactorfields', {
                'FIELDS_MAPPING': [
                    {'expression': "regexp_substr(nationalCadastralReference,'(\\\\d+)')", 'length': 0, 'name': 'SIFKO', 'precision': 0, 'type': 2},
                    {'expression': '"label"', 'length': 0, 'name': 'parcela', 'precision': 0, 'type': 10}], 
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
                    {'expression': '"Parcela in KO"', 'length': 0, 'name': 'Parcela in KO', 'precision': 0, 'type': 10},
                    {'expression': 'round($area,2)', 'length': 0, 'name': 'površina na trasi', 'precision': 0, 'type': 6},
                    {'expression': '"Lastnik"', 'length': 0, 'name': 'Lastnik', 'precision': 0, 'type': 10},
                    {'expression': '"Naslov"', 'length': 0, 'name': 'Naslov', 'precision': 0, 'type': 10},
                    {'expression': '"Dovoljenje"', 'length': 0, 'name': 'Dovoljenje', 'precision': 0, 'type': 10},
                    {'expression': '"Kontakt"', 'length': 0, 'name': 'Kontakt', 'precision': 0, 'type': 10},
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

        #Output summary
        area = 0
        cnt = 0
        for f in refa.getFeatures():
            farea = f['površina na trasi']
            area = f['površina na trasi'] + area
            cnt = cnt + 1
        out_text = self.tr() %(cnt, round(area,2))
        feedback.pushInfo(out_text)

        idx = refa.fields().indexOf('sifko')
        values = refa.uniqueValues(idx)
        #Set treshold to not include parcel 
        prag = 0.5

        for val in values:
            parc_ls = []
            for f in refa.getFeatures():  
                sifko = f['sifko']
                if f['površina na trasi'] > prag and sifko == val:
                    parc_ls.append(f['parcela'])
                    imeko = f['IMEKO']
                else:
                    pass
     
            feedback.pushInfo(out_text_parc)
        
        feedback.pushInfo('''
        Pri tem izpisu niso upoštevane parcele s površino manjšo od %s m2!!!

        *******''' % prag)

        self.dest_id=dest_id
        """
        return {}
        

