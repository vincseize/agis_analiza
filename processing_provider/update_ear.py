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
from ..general_modules import (path,
                               wfs_layer
                        )

from datetime import datetime, date
import os
import base64


class UpdateEar(QgsProcessingAlgorithm):

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
        return UpdateEar()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'update_ear'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Posodobi EAR')

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
        help_text = """To orodje sprejme tabelo iz Accessa (Porocila za SHP) ter posodobi sloj EAR za pregledovalnike.

        Posodabljanje traja okoli ** h. 

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
                self.tr('Porocila za SHP'), 
                optional=True,
                types=[QgsProcessing.TypeVector]
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                'update_only', 
                'Posodobi le območja raziskav',
                 optional=True, 
                 defaultValue=False
            )
        )
   
        self.addParameter(
            QgsProcessingParameterAuthConfig(
                'authentication', 
                'authentication', 
                defaultValue=None
            )
        )

        param = QgsProcessingParameterField('por_stevilka_cpa', 'Porocila_stevilka_CPA', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True, defaultValue='Porocila_stevilka_CPA')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)    
        param = QgsProcessingParameterField('poseg_stevilka_cpa', 'poseg_stevilka_CPA', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='poseg_stevilka_CPA')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('naslov', 'naslov', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='naslov')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('ro', 'ro', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='ro')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('avtorji', 'avtorji', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='avtorji')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('datum', 'datum', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='datum')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('leto', 'leto', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='leto')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('investitor', 'investitor', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='investitor')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('izvajalec', 'izvajalec', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='izvajalec')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('metoda', 'metoda', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='metoda')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('podmetoda', 'podmetoda', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='podmetoda')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('rezultati', 'rezultati', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='rezultati')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('nasutje', 'nasutje', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='nasutje')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('globina', 'globina', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='globina')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('kaj', 'kaj', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='kaj')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField('koda_raziskave', 'koda_raziskave', type=QgsProcessingParameterField.Any, parentLayerParameterName=self.INPUT, allowMultiple=False, optional=True,defaultValue='koda_raziskave')
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

    
        connection = psycopg2.connect(
            host="majadb",
            port="5432", 
            database="CPA_Analiza", 
            user=user, 
            password=password, 
            connect_timeout=1 
        )     
        cursor = connection.cursor()



        if not parameters['update_only']:
            source = self.parameterAsVectorLayer(
                parameters,
                self.INPUT,
                context
            )
            if source is None:
                raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

            if source.featureCount() < 7000:
                #feedback.reportError("Majhno število poročil: %s, preveri vhodni sloj!!" % source.featureCount())
                raise QgsProcessingException("Majhno število poročil: %s, preveri vhodni sloj!!" % source.featureCount())
            
            total = 100.0 / source.featureCount() if source.featureCount() else 0

            feedback.pushInfo('Brišem stare podatke.')
            sql = "TRUNCATE \"Evidenca_arheoloskih_raziskav\".\"Porocila za SHP\" RESTART IDENTITY"
            cursor.execute(sql)
            
            feedback.pushInfo('Vnašam %s posodobljenih vrstic.. (%s)' % (source.featureCount(),str(datetime.now().time())))
            features = source.getFeatures()
            for current, feature in enumerate(features):
                por_stevilka_cpa	=	feature[parameters['por_stevilka_cpa']]
                poseg_stevilka_cpa	=	feature[parameters['poseg_stevilka_cpa']]
                naslov	=	str(feature[parameters['naslov']])
                naslov = naslov.replace("'", "''")
                ro	=	feature[parameters['ro']]
                avtorji	=	feature[parameters['avtorji']]
                datum	=	str(feature[parameters['datum']])
                datum = datum.replace("'", "''")
                leto	=	feature[parameters['leto']]
                investitor	=	feature[parameters['investitor']]
                izvajalec	=	feature[parameters['izvajalec']]
                metoda	=	feature[parameters['metoda']]
                podmetoda	=	feature[parameters['podmetoda']]
                rezultati	=	feature[parameters['rezultati']]
                nasutje	=	feature[parameters['nasutje']]
                globina	=	feature[parameters['globina']]
                kaj	=	feature[parameters['kaj']]
                koda_raziskave	=	feature[parameters['koda_raziskave']]
                sql_insert = "INSERT INTO \"Evidenca_arheoloskih_raziskav\".\"Porocila za SHP\" (\"Porocila_stevilka_CPA\", \"poseg_stevilka_CPA\", naslov, ro, avtorji, datum, leto, investitor, izvajalec, metoda, podmetoda, rezultati, nasutje, globina, kaj, koda_raziskave) VALUES (\'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\', %s, \'%s\', \'%s\', \'%s\', \'%s\', %s, %s, %s, \'%s\', \'%s\')" % (por_stevilka_cpa, poseg_stevilka_cpa, naslov, ro, avtorji, datum, leto, investitor, izvajalec, metoda, podmetoda, rezultati, nasutje, globina, kaj, koda_raziskave)     
                feedback.pushInfo(sql_insert)
                cursor.execute(sql_insert)
                if current % 100 == 0:
                    now = str(datetime.now().time())
                    feedback.pushInfo('Vnešenih %s od %s vrstic (%s)' %(current, source.featureCount(), now))
                feedback.setProgress(int(current * total))
                if feedback.isCanceled():
                    return {}
                feedback.pushInfo('Uspešno vnešenih %s vrstic.' % source.featureCount())
            sql_update_comment = "COMMENT ON TABLE \"Evidenca_arheoloskih_raziskav\".\"Porocila za SHP\" IS \'Datum zadnje posodobitve: %s\.\''" % date.today()
            cursor.execute(sql_update_comment)


        #refresh view+
        refresh_view = "REFRESH MATERIALIZED VIEW CONCURRENTLY public.\"Evidenca arheoloških raziskav\";"
        cursor.execute(refresh_view)
        feedback.pushInfo('Materialized view updated')

        today = date.today()
        sql_update_comment_view = "COMMENT ON MATERIALIZED VIEW public.\"Evidenca arheoloških raziskav\" IS \'Datum zadnje posodobitve: %s. Navajanje vira: Evidenca arheoloških raziskav, Zavod za varstvo kulturne dediščine Slovenije, Center za preventivno arheologijo (podatkovna zbirka).\'" % date.today()
        cursor.execute(sql_update_comment_view)
        connection.commit()

        feedback.pushInfo('Uspešno posodobljeno.' )
        
        return {}
