import xml.etree.ElementTree as ET
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsFields, QgsField, QgsCoordinateReferenceSystem,
    QgsVectorFileWriter, QgsApplication, QgsBlockingNetworkRequest, QgsNetworkRequest
)
from qgis.PyQt.QtCore import QByteArray, QUrl, QObject, QVariant

# Please see https://gis.stackexchange.com/questions/343126/performing-sync-or-async-network-request-in-pyqgis
# for the QgsBlockingNetworkRequest class and QgsNetworkRequest class
# notes on when to use them
class OsmPointsDownloader(QObject):
    def __init__(self, query: str, output_path: str, parent=None):
        """
        :param query: Overpass API query as a string
        :param output_path: File path for saving the output shapefile
        """
        super().__init__(parent)
        self.query = query
        self.output_path = output_path

    def send_query(self):
        """
        Sends the Overpass API query using QgsBlockingNetworkRequest to fetch OSM data synchronously.
        """
        url = QUrl("http://overpass-api.de/api/interpreter")
        request = QgsNetworkRequest(url)
        request.setMethod(QgsNetworkRequest.PostMethod)
        request.setHeader("Content-Type", "application/x-www-form-urlencoded")

        # Send the POST request using QgsBlockingNetworkRequest
        blocking_request = QgsBlockingNetworkRequest()
        reply = blocking_request.fetch(request, QByteArray(self.query.encode('utf-8')))

        # Check for errors in the reply
        if reply.error():
            print(f"Network Error: {reply.errorMessage()}")
        else:
            # Process the response data
            data = reply.content().data().decode('utf-8')
            self.process_data(data)

    def process_data(self, data):
        """
        Processes the XML data returned by Overpass and saves it as a shapefile.
        :param data: XML response as a string
        """
        # Parse the XML
        root = ET.fromstring(data)

        # Create a new layer to store the footways
        crs = QgsCoordinateReferenceSystem(4326)  # WGS 84
        layer = QgsVectorLayer("LineString?crs=EPSG:4326", "Footways", "memory")
        pr = layer.dataProvider()

        # Add attributes
        pr.addAttributes([QgsField("osm_id", QVariant.String)])
        layer.updateFields()

        # Iterate over the ways and extract coordinates
        for way in root.findall(".//way"):
            osm_id = way.get('id')
            coords = []
            for nd in way.findall("nd"):
                ref = nd.get('ref')
                node = root.find(f".//node[@id='{ref}']")
                lat = float(node.get('lat'))
                lon = float(node.get('lon'))
                coords.append(QgsPointXY(lon, lat))

            # Create a feature
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPolylineXY(coords))
            feature.setAttributes([osm_id])
            pr.addFeatures([feature])

        # Add the layer to the QGIS project
        QgsProject.instance().addMapLayer(layer)

        # Save to a shapefile
        QgsVectorFileWriter.writeAsVectorFormat(layer, self.output_path, "UTF-8", crs, "ESRI Shapefile")
        print(f"Shapefile saved to {self.output_path}")
