from qgis.core import QgsProcessingProvider
from PyQt5.QtGui import QIcon
import os

#import algorithm
#from .fileslist import Files2Table
#from .katvkat import IzvoziKatalogVWord
#from .se_catalog import IzvoziKatalogSeVWord
from .seznam_parcel import SeznamParcelZnotrajObmojaRaziskave


class Provider(QgsProcessingProvider):
    def __init__(self):
        self.plugin_dir = os.path.dirname(__file__)
        QgsProcessingProvider.__init__(self)
        
    def loadAlgorithms(self, *args, **kwargs):
        #self.addAlgorithm(Files2Table())
        #self.addAlgorithm(IzvoziKatalogVWord())
        self.addAlgorithm(SeznamParcelZnotrajObmojaRaziskave())
        # add additional algorithms here
        # self.addAlgorithm(MyOtherAlgorithm())

        
    def id(self):
        return 'agis_analiza'
        
    def name(self, *args, **kwargs):
        """The human friendly name of your plugin in Processing.

        This string should be as short as possible (e.g. "Lastools", not
        "Lastools version 1.0.1 64-bit") and localised.
        """
        return self.tr('AGIS analiza')

    def icon(self):
        """Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QIcon(os.path.join(os.path.dirname(__file__),'icon.png'))
        