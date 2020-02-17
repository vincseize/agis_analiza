from pathlib import Path
from qgis.core import (QgsDataSourceUri,
                       QgsApplication,
					   QgsVectorLayer
                       )



p_app = Path(QgsApplication.qgisSettingsDirPath())
p_plugin = p_app/"python/plugins/agis_analiza"
p_styles = p_plugin/"styles"

style_parcele = p_styles/"Seznam parcel_dovoljenja.qml"


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



""""
#test server
def postgres():
    uri = QgsDataSourceUri()
    host = "localhost"
    database = "test"
    user = "postgres"
    password = "postgres"
    port = '5432'
    uri.setConnection(host, port, database, user, password)
    return uri

def postgres_layer():
    uri = postgres()
    uri.setDataSource('test', 'ttt', 'geom',"", "id")
    parcele = QgsVectorLayer(uri.uri(), "parcele", "postgres")
    return parcele
"""
