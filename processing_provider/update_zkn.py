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

from datetime import date
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
                defaultValue=''
            )
        )
        
        
        param = QgsProcessingParameterField('pc_mid', 'PS_MID', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, defaultValue='PC_MID')
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
        param = QgsProcessingParameterField('sys', 'SYS_ODDTM', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, defaultValue='SYS_ODDTM')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        
        

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        feedback = QgsProcessingMultiStepFeedback(1, feedback)

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
            feedback.reportError("Majhno število parcel: %s, preveri vhodni sloj!!" % source.featureCount())
            #raise QgsProcessingException("Majhno število parcel: %s, preveri vhodni sloj!!" % source.featureCount())
            

        total = 100.0 / source.featureCount() if source.featureCount() else 0

        connection = psycopg2.connect(
            host="majadb",
            port="5432", 
            database="CPA_Analiza", 
            user=user, 
            password=password, 
            connect_timeout=1 
        )     
        
        cursor = connection.cursor()
        sql = "TRUNCATE \"CPA\".\"ZKN parcele_gurs\" RESTART IDENTITY"
        cursor.execute(sql)
      
        features = source.getFeatures()
        for current, feature in enumerate(features):
            pc_mid = feature[parameters['pc_mid']]
            sifko = feature[parameters['sifko']]
            parcela = feature[parameters['parcela']]
            vrstap = feature[parameters['vrstap']]
            rang = feature[parameters['rang']]
            sys_oddtm = feature[parameters['sys']] 
            sys_oddtm = str(sys_oddtm)
            geom = feature.geometry()
            sql_insert = "INSERT INTO \"CPA\".\"ZKN parcele_gurs\" (pc_mid, sifko, parcela, vrstap, rang, sys_oddtm, geom) VALUES (%s, %s, %s, %s, %s, \'%s\', ST_GeomFromText(\'%s\', 3794))" % (pc_mid, sifko, parcela, vrstap, rang, sys_oddtm,geom.asWkt())
            cursor.execute(sql_insert)
            feedback.setProgress(int(current * total))
 
        today = date.today()
        sql_update_comment = "COMMENT ON TABLE \"CPA\".\"ZKN parcele_gurs\" IS \'Zemljiško katasterski načrt, parcele. Vir podatka: https://egp.gu.gov.si/egp/dd. Datum zadnje posodobitve: %s\'" % date.today()
        cursor.execute(sql_update_comment)
        connection.commit()

        feedback.pushInfo('Uspešno posodobljeno, vnešenih %s parcel.' % source.featureCount())
        return {}