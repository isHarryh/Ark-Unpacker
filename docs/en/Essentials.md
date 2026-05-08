Additional Documentation for ArkUnpacker

# Prerequisites

## RGB Channels and Alpha Channel Images

Most images in Arknights (such as character illustrations and chibi models) are not extracted as a single image from AB files, but as two separate images: a color image (referred to as the RGB channel image) and a grayscale image (referred to as the Alpha channel image, usually with "alpha" in the filename).

In the Alpha channel image, pure white areas represent fully opaque regions, while pure black areas represent fully transparent regions. To obtain a complete image with both color and transparency, these images need to be merged.

One of the features of this tool is to automatically detect Alpha channel images, locate their corresponding RGB channel images, merge them, and save the final result.

## Spine Animated Characters

The chibi characters in Arknights are implemented using [Spine animation](http://esotericsoftware.com), specifically version 3.8.

A complete Spine animation model in Arknights typically consists of three types of files: **PNG images** containing individual assets, **atlas files** that define the positions of those assets within the images, and **skel files** that store skeletal animation data. In some cases, a model may include multiple PNG images, and some skel files may be in JSON format.

It is important to note that operator battle chibi models have both front and back versions, but in AB files, they share identical filenames. In some cases, base (infrastructure) chibi models may also share the same names as battle models. As a result, standard unpacking methods may not correctly export Spine animation models.

By using the dedicated Spine model export mode, these types can be accurately distinguished and organized into separate folders during extraction, for example:

- `BattleFront` Front-facing battle chibi  
- `BattleBack` Back-facing battle chibi  
- `Building` Operator base chibi  
- `DynIllust` Dynamic illustrations  
- `DynIllustStart` Dynamic illustration entry animations  
- `DynPortrait` Dynamic illustration portraits  