import os
import tempfile
import textwrap

import numpy as np
from pytest import approx

from pgimp.GimpFile import GimpFile, LayerType, ColorMap
from pgimp.GimpScriptRunner import GimpScriptRunner
from pgimp.util import file


rgb_file = GimpFile(file.relative_to(__file__, 'test-resources/rgb.xcf'))
"""
The file rgb.xcf contains a 3x2 image with white 'Background' layer and 'Red', 'Green', 'Blue' layers with differing 
opacity. The layer 'Background' contains a black pixel at y=0, x=1, the others pixels are white.
"""
black_and_yellow_file = GimpFile(file.relative_to(__file__, 'test-resources/black_and_yellow.xcf'))
"""
The 3x2 image file black_and_yellow.xcf contains a 'Background' layer that is black and a 'Yellow' layer that is 
yellow rgb(240, 255, 0).
"""


def test_layer_to_numpy():
    actual = rgb_file.layer_to_numpy('Background')
    expected = np.array([
        [[255, 255, 255], [0, 0, 0], [255, 255, 255]],
        [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
    ], dtype=np.uint8)

    assert np.all(expected == actual)
    assert actual.shape == (2, 3, 3)


def test_create():
    filename = file.relative_to(__file__, 'test-resources/test-create.xcf')
    layer_bg = np.array([
        [[255, 255, 255], [0, 0, 0], [255, 255, 255]],
        [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
    ], dtype=np.uint8)

    gimp_file = GimpFile(filename)
    gimp_file.create('Background', layer_bg)

    exists = os.path.exists(filename)
    actual = gimp_file.layer_to_numpy('Background')
    os.remove(filename)

    assert exists
    assert np.all(layer_bg == actual)


def test_numpy_to_layer():
    tmp_file = tempfile.mktemp(suffix='.xcf')
    layer_bg = np.array([
        [[255, 255, 255], [0, 0, 0], [255, 255, 255]],
        [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
    ], dtype=np.uint8)
    layer_fg = np.array([
        [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
        [[255, 255, 255], [0, 0, 0], [255, 255, 255]],
    ], dtype=np.uint8)

    gimp_file = GimpFile(tmp_file)
    gimp_file.create('Background', layer_bg)
    gimp_file.numpy_to_layer('Foreground', layer_fg, opacity=55., visible=False)

    actual_bg = gimp_file.layer_to_numpy('Background')
    actual_fg = gimp_file.layer_to_numpy('Foreground')

    os.remove(tmp_file)

    assert np.all(layer_bg == actual_bg)
    assert np.all(layer_fg == actual_fg)


def test_add_layer_from():
    tmp_file = tempfile.mktemp(suffix='.xcf')
    layer_bg = np.array([
        [[255, 255, 255], [0, 0, 0], [255, 255, 255]],
        [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
    ], dtype=np.uint8)
    position = 1

    gimp_file = GimpFile(tmp_file)
    gimp_file.create('Background', layer_bg)
    gimp_file.add_layer_from(black_and_yellow_file, 'Yellow', new_name='Yellow (copied)', new_position=position)

    assert 'Yellow (copied)' == gimp_file.layers()[position].name
    assert np.all([240, 255, 0] == gimp_file.layer_to_numpy('Yellow (copied)'))

    os.remove(tmp_file)


def test_merge_layer_from():
    tmp_file = tempfile.mktemp(suffix='.xcf')
    layer_bg = np.array([
        [[255, 255, 255], [0, 0, 0], [255, 255, 255]],
        [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
    ], dtype=np.uint8)

    gimp_file = GimpFile(tmp_file)
    gimp_file.create('Yellow', layer_bg)
    gimp_file.merge_layer_from(black_and_yellow_file, 'Yellow')

    new_layer_contents = gimp_file.layer_to_numpy('Yellow')

    os.remove(tmp_file)

    assert np.all([240, 255, 0] == new_layer_contents)


def test_layers():
    layers = rgb_file.layers()

    assert ['Blue', 'Green', 'Red', 'Background'] == list(map(lambda x: x.name, layers))
    assert [0, 1, 2, 3] == list(map(lambda x: x.position, layers))
    assert [False, False, False, True] == list(map(lambda x: x.visible, layers))
    assert [23.92156862745098, 40.3921568627451, 52.54901960784314, 100.0] == list(map(lambda x: approx(x.opacity), layers))


def test_convert_to_indexed_using_predefined_colormap():
    tmp_file = tempfile.mktemp(suffix='.xcf')
    values = np.array([[i for i in range(0, 256)]], dtype=np.uint8)
    assert (1, 256) == values.shape

    gimp_file = GimpFile(tmp_file)
    gimp_file.create_indexed('Background', values, ColorMap.JET)
    gimp_file.numpy_to_layer('Values', values, type=LayerType.INDEXED)

    layer_bg = gimp_file.layer_to_numpy('Background')
    layer_values = gimp_file.layer_to_numpy('Values')

    os.remove(tmp_file)

    assert (1, 256, 1) == layer_bg.shape
    assert np.all(values == layer_bg[:, :, 0])
    assert (1, 256, 1) == layer_values.shape
    assert np.all(values == layer_values[:, :, 0])


def test_convert_to_indexed_using_custom_colormap():
    tmp_file = tempfile.mktemp(suffix='.xcf')
    values = np.array([[i for i in range(0, 256)]], dtype=np.uint8)
    assert (1, 256) == values.shape
    colormap = np.array([[255, 0, 0], [0, 255, 0], [0, 0, 255], *[[i, i, i] for i in range(3, 256)]], dtype=np.uint8)
    assert (256, 3) == colormap.shape

    gimp_file = GimpFile(tmp_file)
    gimp_file.create_indexed('Background', values, colormap=colormap)
    gimp_file.numpy_to_layer('Values', values, type=LayerType.INDEXED)

    layer_bg = gimp_file.layer_to_numpy('Background')
    layer_values = gimp_file.layer_to_numpy('Values')

    os.remove(tmp_file)

    assert (1, 256, 1) == layer_bg.shape
    assert np.all(values == layer_bg[:, :, 0])
    assert (1, 256, 1) == layer_values.shape
    assert np.all(values == layer_values[:, :, 0])