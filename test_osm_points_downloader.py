import os
import unittest
from unittest.mock import patch, MagicMock
from osm_downloader import OsmPointsDownloader


class TestOsmPointsDownloader(unittest.TestCase):
    def setUp(self):
        """
        Set up the environment before each test.
        """
        self.query = """
        [out:xml] [timeout:25]; 
        {{geocodeArea:Saint Lucia}} -> .area_0;
        (
            node["highway"="footway"](area.area_0);
            way["highway"="footway"](area.area_0);
            relation["highway"="footway"](area.area_0);
        );
        (._;>;);
        out body;
        """
        self.output_path = "/tmp/test_footways.shp"
        self.fetcher = OsmPointsFetcher(self.query, self.output_path)

    @patch("OSMPointsFetcher.QgsBlockingNetworkRequest.fetch")
    @patch("OSMPointsFetcher.QgsVectorFileWriter.writeAsVectorFormat")
    def test_send_query_and_process_data(self, mock_writer, mock_fetch):
        """
        Test the send_query method and the processing of OSM data.
        """
        # Mock the network response
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

        # Call the method to trigger the Overpass query
        self.fetcher.send_query()

        # Validate that the shapefile writer was called
        mock_writer.assert_called_once_with(
            mock.ANY,  # This checks if any layer was passed
            self.output_path, "UTF-8", mock.ANY, "ESRI Shapefile"
        )

        # Check that the file was saved to the correct path
        self.assertTrue(os.path.exists(self.output_path))

    def tearDown(self):
        """
        Clean up after each test.
        """
        if os.path.exists(self.output_path):
            os.remove(self.output_path)


if __name__ == "__main__":
    unittest.main()
