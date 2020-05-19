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
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterAuthConfig,         
                       QgsAuthMethodConfig,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFile
                     
                    
                       )
import processing
import psycopg2
from pathlib import Path
from ..general_modules import (pg_connect)


from datetime import datetime, date, timedelta
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
        help_text = """To orodje sprejme ZKN ter ga posodobi v podatkovni bazi. Sveži podatki se pridobijo na https://egp.gu.gov.si/egp/.

        Posodabljanje traja okoli 145 min, močno ne obremeni sistema vendar začasno onemogoči uporabo sloja drugim uporabnikom! 

        Vse spremembe so potrjene po uspešnem postopku, ob vmesni prekinitvi se sloj vrne v prvotno stanje. 
        
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
        
        self.addParameter(
            QgsProcessingParameterAuthConfig(
                'authentication', 
                'authentication', 
                defaultValue=None
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

        auth_method_id = self.parameterAsString(
            parameters,
            'authentication',
            context
        )
        # get the application's authenticaion manager
        auth_mgr = QgsApplication.authManager()
        # create an empty authmethodconfig object
        auth_cfg = QgsAuthMethodConfig()
        # load config from manager to the new config instance and decrypt sensitive data
        auth_mgr.loadAuthenticationConfig(auth_method_id, auth_cfg, True)
        # get the configuration information (including username and password)
        auth = auth_cfg.configMap()

        password = auth["password"]
        user = auth["username"]
        
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsVectorLayer(
            parameters,
            self.INPUT,
            context
        )
    
        if 'ZKN' in str(source.name()):  
            feedback.pushInfo('Pravi sloj')   
        else:
            raise QgsProcessingException("Napačen sloj? Vhodni sloj v imenu ne vsebuje \"ZKN\"!")


        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
   
        if source.featureCount() < 3000000:
            #feedback.reportError("Majhno število parcel: %s, preveri vhodni sloj!!" % source.featureCount())
            raise QgsProcessingException("Majhno število parcel: %s, preveri vhodni sloj!!" % source.featureCount())
            

        total = 100.0 / source.featureCount() if source.featureCount() else 0

        connection = pg_connect(self, user, password)
        
        feedback.pushInfo('Brišem stare podatke.')
        cursor = connection.cursor()
        sql = "TRUNCATE \"Podlage\".\"ZKN parcele_gurs\" RESTART IDENTITY"
        cursor.execute(sql)
        starttime = datetime.now()
        feedback.pushInfo('Vnašam %s novih parcel.. (%s)' % (source.featureCount(),str(starttime.time())))
        features = source.getFeatures()
        for current, feature in enumerate(features):
            pc_mid = feature[parameters['pc_mid']]
            sifko = feature[parameters['sifko']]
            parcela = feature[parameters['parcela']]
            vrstap = feature[parameters['vrstap']]
            rang = feature[parameters['rang']]
            sys_oddtm = feature[parameters['sys']] 
            sys = sys_oddtm.toString('yyyy-MM-dd')
            geom = feature.geometry()
            sql_insert = "INSERT INTO \"Podlage\".\"ZKN parcele_gurs\" (sifko, parcela, vrstap, rang, sys_oddtm, geom) VALUES (%s, \'%s\', %s, %s, \'%s\', ST_GeomFromText(\'%s\', 3794))" % (sifko, parcela, vrstap, rang, sys, geom.asWkt())
            cursor.execute(sql_insert)
            if current % 100000 == 0 and current != 0:            
                time_diff = datetime.now() - starttime
                duration_s = (source.featureCount() * time_diff.total_seconds())  / current
                est_dur = timedelta(seconds=duration_s) - time_diff
                estimated_dur = int(est_dur.total_seconds()/ 60)
                feedback.pushDebugInfo('%s:' % str(datetime.now()))
                feedback.pushInfo('Vnešenih %s od %s parcel. Ocenjen čas do zaključka: %s min.\n' %(current, source.featureCount(), str(estimated_dur)))

            
            feedback.setProgress(int(current * total))
            if feedback.isCanceled():
                return {}
                
        today = date.today()
        sql_update_comment = "COMMENT ON TABLE \"Podlage\".\"ZKN parcele_gurs\" IS \'Zemljiško katasterski načrt, parcele. Vir podatka: https://egp.gu.gov.si/egp/. Datum zadnje posodobitve: %s.\'" % date.today()
        cursor.execute(sql_update_comment)
        connection.commit()


        #refresh view comment
        sql_update_view_comment = "COMMENT ON VIEW \"public\".\"ZKN parcele\" IS \'Zemljiško katasterski načrt, parcele. Vir podatka: https://egp.gu.gov.si/egp/. Datum zadnje posodobitve: %s.\'" % date.today()
        cursor.execute(sql_update_view_comment)

        feedback.pushInfo('View updated')

        feedback.pushInfo('Uspešno posodobljeno, vnešenih %s parcel. (%s)' % (source.featureCount(), starttime.time()))
        return {}
