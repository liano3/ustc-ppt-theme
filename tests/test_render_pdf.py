import importlib.util
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET

spec = importlib.util.spec_from_file_location(
    'render_pdf', Path(__file__).resolve().parents[1] / 'scripts/render_pdf.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class FontConfigTests(unittest.TestCase):
    def test_prefers_template_font_when_installed(self):
        self.assertEqual(renderer.choose_cjk('PingFang SC,苹方-简\nMicrosoft YaHei,微软雅黑'),
                         'Microsoft YaHei')

    def test_mac_fallback_and_case_insensitive_alias(self):
        self.assertEqual(renderer.choose_cjk('PingFang SC,苹方-简'), 'PingFang SC')
        self.assertEqual(renderer.choose_cjk('Noto Sans CJK SC', 'noto sans cjk sc'),
                         'noto sans cjk sc')

    def test_missing_font_is_not_silently_substituted(self):
        for requested in (None, 'Microsoft YaHei'):
            with self.assertRaises(ValueError):
                renderer.choose_cjk('Arial\nDejaVu Sans', requested)

    def test_mapping_escapes_paths_and_family_names(self):
        root = ET.fromstring(renderer.font_config(Path('/tmp/A & B'), 'CJK & Font'))
        self.assertEqual(root.find('cachedir').text, '/tmp/A & B')
        self.assertEqual(root.find('match/test/string').text, 'Microsoft YaHei')
        self.assertEqual(root.find('match/edit/string').text, 'CJK & Font')

    def test_no_self_alias_when_yahei_is_available(self):
        root = ET.fromstring(renderer.font_config(Path('/tmp/cache'), 'Microsoft YaHei'))
        self.assertIsNone(root.find('match'))


if __name__ == '__main__':
    unittest.main()
