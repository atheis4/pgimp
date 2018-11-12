import numpy as np

import gimp
import gimpenums


def copy_layer(image_src, layer_name_src, image_dst, layer_name_dst, position_dst=0):
    """
    :type image_src: gimp.Image
    :type layer_name_src: str
    :type image_dst: gimp.Image
    :type layer_name_dst: str
    :type position_dst: int
    """
    layer_src = gimp.pdb.gimp_image_get_layer_by_name(image_src, layer_name_src)
    layer_dst = gimp.pdb.gimp_image_get_layer_by_name(image_dst, layer_name_dst)
    if layer_dst is None:
        layer_dst = gimp.pdb.gimp_layer_new(
            image_dst,
            layer_src.width,
            layer_src.height,
            layer_src.type,
            layer_name_dst,
            layer_src.opacity,
            layer_src.mode
        )
        gimp.pdb.gimp_image_add_layer(image_dst, layer_dst, 0)

    gimp.pdb.gimp_edit_copy(layer_src)
    layer_floating = gimp.pdb.gimp_edit_paste(layer_dst, True)
    gimp.pdb.gimp_floating_sel_anchor(layer_floating)
    reorder_layer(image_dst, layer_dst, position_dst)


def reorder_layer(image, layer, position):
    """
    :type image: gimp.Image
    :type layer: gimp.Layer
    :type position: int
    """
    gimp.pdb.gimp_image_reorder_item(image, layer, None, position)


def merge_mask_layer(image_src, layer_name_src, image_dst, layer_name_dst, mask_foreground_color, position_dst=0):
    """
    :type image_src: gimp.Image
    :type layer_name_src: str
    :type image_dst: gimp.Image
    :type layer_name_dst: str
    :type mask_foreground_color: int
    :type position_dst: int
    """
    if mask_foreground_color not in [0, 1]:
        raise ValueError('Mask foreground color must be 1 for white and 0 for black')
    if image_dst.base_type != image_src.base_type:
        raise ValueError('Image types must match')
    if image_src.base_type == gimpenums.RGB:
        bpp = 3
    elif image_src.base_type == gimpenums.GRAY:
        bpp = 1
    else:
        raise ValueError('Image must be rgb or gray')

    layer_src = gimp.pdb.gimp_image_get_layer_by_name(image_src, layer_name_src)
    layer_dst = gimp.pdb.gimp_image_get_layer_by_name(image_dst, layer_name_dst)

    if layer_src is None:
        if mask_foreground_color == 1:  # white
            content_src = np.zeros(shape=(image_dst.height, image_dst.width))
        else:  # black
            content_src = np.ones(shape=(image_dst.height, image_dst.width))*255
    else:
        region = layer_src.get_pixel_rgn(0, 0, layer_src.width, layer_src.height)
        buffer = region[:, :]
        content_src = np.frombuffer(buffer, dtype=np.uint8).reshape((layer_src.height, layer_src.width, bpp))

    if layer_dst is None:
        if mask_foreground_color == 1:  # white
            content_dst = np.zeros(shape=(image_dst.height, image_dst.width))
        else:  # black
            content_dst = np.ones(shape=(image_dst.height, image_dst.width))*255
    else:
        region = layer_dst.get_pixel_rgn(0, 0, layer_dst.width, layer_dst.height)
        buffer = region[:, :]
        content_dst = np.frombuffer(buffer, dtype=np.uint8).reshape((layer_dst.height, layer_dst.width, bpp))

    if mask_foreground_color == 1:  # white
        content_merged = np.maximum(content_src, content_dst).astype(np.uint8)
    else:  # black
        content_merged = np.minimum(content_src, content_dst).astype(np.uint8)

    if layer_dst is None:
        if image_src.base_type == gimpenums.RGB:  # rgb
            layer_type = gimpenums.RGB_IMAGE
        else:  # gray
            layer_type = gimpenums.GRAY_IMAGE

        layer_dst = gimp.pdb.gimp_layer_new(
            image_dst,
            content_merged.shape[1],
            content_merged.shape[0],
            layer_type,
            layer_name_dst,
            100,
            gimpenums.NORMAL_MODE
        )
        gimp.pdb.gimp_image_add_layer(image_dst, layer_dst, 0)

    layer_dst.get_pixel_rgn(0, 0, layer_dst.width, layer_dst.height)[:, :] = content_merged.tobytes()
    reorder_layer(image_dst, layer_dst, position_dst)