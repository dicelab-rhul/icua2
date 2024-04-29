import unittest
from pathlib import Path
from lxml import etree
from ast import literal_eval
from icua2.utils import TaskLoader


def get_path(directory):
    return Path(__file__).parent / directory


def to_literal(value):
    try:
        return literal_eval(value)
    except:
        return value


NAME = "task"


class TestTaskLoader(unittest.TestCase):

    def test_svg_template(self):
        loader = TaskLoader()
        path = get_path("svg_template")
        loader.register_task(NAME, path, enable_dynamic_loading=True)


# class TestTaskLoader(unittest.TestCase):

#     def test_load_error_no_files(self):
#         loader = MultiTaskLoader()
#         task_directory = get_path("svg_empty")
#         with self.assertRaises(FileNotFoundError):
#             loader.load_task(task_directory, name=NAME)

#     def test_svg_template(self):
#         loader = MultiTaskLoader()
#         context = {"task_name": "task_override"}

#         task_directory = get_path("svg_template")
#         loader.load_task(task_directory, name=NAME, context=context)
#         task1 = loader.get_task(NAME)

#         loader = MultiTaskLoader()
#         schema_file = task_directory / "task.schema.json"
#         context_file = task_directory / "task.json"
#         file = task_directory / "task.svg.jinja"
#         loader.load_task(
#             path=file,
#             context_file=context_file,
#             schema_file=schema_file,
#             context=context,
#         )
#         task2 = loader.get_task(NAME)
#         self.assertEqual(task1, task2)

#         root = etree.fromstring(task1)
#         svg = {k: to_literal(v) for k, v in root.attrib.items()}
#         cir = {k: to_literal(v) for k, v in root.getchildren()[0].attrib.items()}
#         self.assertDictEqual(
#             svg,
#             {
#                 "id": "task_override",
#                 "x": 10,
#                 "y": 10,
#                 "width": 320,
#                 "height": 320,
#             },
#         )
#         self.assertDictEqual(
#             cir,
#             {
#                 "cx": 170,
#                 "cy": 170,
#                 "r": 10,
#                 "stroke": "#ffffff",
#                 "stroke-width": 2,
#                 "fill": "#000000",
#             },
#         )

#     def test_svg(self):
#         loader = MultiTaskLoader()
#         task_directory = get_path("svg")
#         loader.load_task(task_directory, name=NAME)
#         task = loader.get_task(NAME)
#         print(task)
#         root = etree.fromstring(task)
#         svg = {k: to_literal(v) for k, v in root.attrib.items()}
#         cir = {k: to_literal(v) for k, v in root.getchildren()[0].attrib.items()}
#         self.assertDictEqual(
#             svg,
#             {
#                 "id": "task",
#                 "x": 10,
#                 "y": 10,
#                 "width": 320,
#                 "height": 320,
#             },
#         )
#         self.assertDictEqual(
#             cir,
#             {
#                 "cx": 170,
#                 "cy": 170,
#                 "r": 10,
#                 "stroke": "#ffffff",
#                 "stroke-width": 2,
#                 "fill": "#000000",
#             },
#         )

#     def test_svg_template_context_only(self):
#         loader = MultiTaskLoader()
#         task_directory = get_path("svg_template_context_only")
#         loader.load_task(task_directory, name=NAME)
#         task = loader.get_task(NAME)
#         root = etree.fromstring(task)
#         svg = {k: to_literal(v) for k, v in root.attrib.items()}
#         cir = {k: to_literal(v) for k, v in root.getchildren()[0].attrib.items()}
#         self.assertDictEqual(
#             svg, {"id": "task", "x": 10, "y": 10, "width": 100, "height": 100}
#         )
#         self.assertDictEqual(
#             cir,
#             {
#                 "cx": 60,
#                 "cy": 60,
#                 "r": 10,
#                 "stroke": "#ffffff",
#                 "stroke-width": 2,
#                 "fill": "#000000",
#             },
#         )

#     def test_svg_template_schema_only(self):
#         loader = MultiTaskLoader()
#         task_directory = get_path("svg_template_schema_only")
#         loader.load_task(task_directory, name=NAME)
#         task = loader.get_task(NAME)
#         root = etree.fromstring(task)
#         svg = {k: to_literal(v) for k, v in root.attrib.items()}
#         cir = {k: to_literal(v) for k, v in root.getchildren()[0].attrib.items()}
#         self.assertDictEqual(
#             svg, {"id": "task", "x": 0, "y": 0, "width": 320, "height": 320}
#         )
#         self.assertDictEqual(
#             cir,
#             {
#                 "cx": 160,
#                 "cy": 160,
#                 "r": 20,
#                 "stroke": "#1d90ff",
#                 "stroke-width": 2,
#                 "fill": "#1d90ff",
#             },
#         )


if __name__ == "__main__":
    unittest.main()
