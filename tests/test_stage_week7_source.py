import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from stage_week7_source import map_target


class StageWeek7Tests(unittest.TestCase):
    def test_known_service(self):
        self.assertEqual(map_target('parent/amazon_search_service/main.py').name, 'main.py')

    def test_no_traversal(self):
        self.assertIsNone(map_target('../app.py'))

    def test_no_models(self):
        self.assertIsNone(map_target('foo/artifacts/lambdamart_model.txt'))
        self.assertIsNone(map_target('foo/data/catalog.parquet'))

    def test_streamlit(self):
        self.assertEqual(map_target('package/streamlit_app.py').name, 'streamlit_app.py')

    def test_no_unrelated_sources(self):
        self.assertIsNone(map_target('package/results/benchmark.py'))


if __name__ == '__main__':
    unittest.main()
