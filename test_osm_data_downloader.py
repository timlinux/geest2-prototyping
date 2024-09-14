import unittest
from unittest.mock import patch, MagicMock
import os
from osm_data_downloader import OsmDataDownloader  # Assuming the class is saved in OsmDataDownloader.py

class TestOsmDataDownloader(unittest.TestCase):
    def setUp(self):
        """
        Set up the environment before each test.
        """
        # Example query for line data (footpaths)
        self.footpath_query = """
        [out:xml] [timeout:25];
        (
          way["highway"="footway"](area:3600324331);
        );
        (._;>;);
        out body;
        """

        # Example query for polygon data (buildings)
        self.building_query = """
        [out:xml] [timeout:25];
        (
          way["building"](area:3600324331);
        );
        (._;>;);
        out body;
        """

        self.footpath_output_path = "/tmp/test_footpaths.shp"
        self.building_output_path = "/tmp/test_buildings.shp"
        
        # Create OsmDataDownloader instances for footpaths and buildings
        self.footpath_downloader = OsmDataDownloader(query=self.footpath_query, output_path=self.footpath_output_path)
        self.building_downloader = OsmDataDownloader(query=self.building_query, output_path=self.building_output_path)

    @patch("OsmDataDownloader.QgsBlockingNetworkRequest.fetch")
    @patch("OsmDataDownloader.QgsVectorFileWriter.writeAsVectorFormat")
    def test_download_line_data(self, mock_writer, mock_fetch):
        """
        Test the download_line_data method and ensure line-based data is processed correctly.
        """
        # Mock network response for line data (footpaths)
        mock_reply = MagicMock()
        mock_reply.error.return_value = False
        mock_reply.content().data.return_value = """
        <osm>
          <node id="1" lat="14.01" lon="-60.98"/>
          <node id="2" lat="14.02" lon="-60.99"/>
          <way id="123">
            <nd ref="1"/>
            <nd ref="2"/>
          </way>
        </osm>
        """
        mock_fetch.return_value = mock_reply

        # Call the method to trigger the Overpass query for line data
        self.footpath_downloader.download_line_data()

        # Validate that the shapefile writer was called for line data
        mock_writer.assert_called_once_with(
            mock.ANY,  # This checks if any layer was passed
            self.footpath_output_path, "UTF-8", mock.ANY, "ESRI Shapefile"
        )

        # Check that the file was saved to the correct path
        self.assertTrue(os.path.exists(self.footpath_output_path))

    @patch("OsmDataDownloader.QgsBlockingNetworkRequest.fetch")
    @patch("OsmDataDownloader.QgsVectorFileWriter.writeAsVectorFormat")
    def test_download_polygon_data(self, mock_writer, mock_fetch):
        """
        Test the download_polygon_data method and ensure polygon-based data is processed correctly.
        """
        # Mock network response for polygon data (buildings)
        mock_reply = MagicMock()
        mock_reply.error.return_value = False
        mock_reply.content().data.return_value = """
        <osm>
          <node id="1" lat="14.01" lon="-60.98"/>
          <node id="2" lat="14.02" lon="-60.99"/>
          <way id="123">
            <nd ref="1"/>
            <nd ref="2"/>
            <nd ref="1"/> <!-- Closing the polygon -->
          </way>
        </osm>
        """
        mock_fetch.return_value = mock_reply

        # Call the method to trigger the Overpass query for polygon data
        self.building_downloader.download_polygon_data()

        # Validate that the shapefile writer was called for polygon data
        mock_writer.assert_called_once_with(
            mock.ANY,  # This checks if any layer was passed
            self.building_output_path, "UTF-8", mock.ANY, "ESRI Shapefile"
        )

        # Check that the file was saved to the correct path
        self.assertTrue(os.path.exists(self.building_output_path))

    def tearDown(self):
        """
        Clean up after each test.
        """
        if os.path.exists(self.footpath_output_path):
            os.remove(self.footpath_output_path)

        if os.path.exists(self.building_output_path):
            os.remove(self.building_output_path)


if __name__ == "__main__":
    unittest.main()
