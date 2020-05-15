import os
from pathlib import Path
from qgis.core import (QgsProject,
                       QgsRasterLayer,
                       QgsVectorLayer,
                       QgsLayerDefinition,
                       QgsDataSourceUri,
                       QgsProcessingMultiStepFeedback
                       )
import psycopg2

def path(item):
    path = {}
    plugin_dir = os.path.dirname(__file__)

    path['plugin'] = Path(plugin_dir)
    path['styles'] = path['plugin']/"styles"
    path['icons'] = path['plugin']/"icons"

    path = path[item]
    return path



def pg_connect(self, user, password):
    connection = psycopg2.connect(
        host="majadb",
        port="5432", 
        database="CPA_Analiza", 
        user=user, 
        password=password, 
        connect_timeout=1 
    )     
    return connection


def wfs_layer(self, name, typename, crs, url, sql):
    uri = QgsDataSourceUri()
    uri.setParam('service', 'WFS')
    uri.setParam('restrictToRequestBBOX', '1') 
    uri.setParam('request', 'GetFeature')
    uri.setParam('version', 'auto')
    uri.setParam('typename', typename)
    uri.setParam('srsName', crs)
    uri.setParam('url', url)
    uri.setSql(sql)
    wfs_layer = QgsVectorLayer(uri.uri(), name, 'WFS')
    return wfs_layer

# Checks if connected to CPA, ZVKDS network
def access(self):
    self.host = "majadb"
    self.database = "CPA_Analiza"
    self.user = "cpa"
    self.password = "cpa"
    self.port = "5432"
    try:
        conn = psycopg2.connect(host=self.host,port=self.port, database=self.database, user=self.user, password=self.password, connect_timeout=1 )
        conn.close()
        return True
    except:
        return False

# Get layer from CPA, ZVKDS database
def postgis_connect(self, shema, tablename, geometry, id):
    uri = QgsDataSourceUri()
    uri.setConnection(self.host, self.port, self.database, self.user, self.user)  
    uri.setDataSource(shema, tablename, geometry)
    uri.setKeyColumn(id)
    vlayer=QgsVectorLayer (uri .uri(False), tablename, "postgres")
    return vlayer
        
"""
def postgres():
    uri = QgsDataSourceUri()
    host = "majadb"
    database = "CPA_Analiza"
    user = "cpa"
    password = "cpa"
    port = '5432'
    uri.setConnection(host, port, database, user, password)
    return uri

def postgres_layer():
    uri = postgres()
    uri.setDataSource('public', 'Parcele', 'geom',"", "id")
    parcele = QgsVectorLayer(uri.uri(), "parcele", "postgres")
    return parcele


 

"""