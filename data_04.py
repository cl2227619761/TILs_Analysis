'''
divide whole slide image into tiles and save the tiles into local disk

background tiles are removed based on some criteira (see code)

purpose: tiling the whole slide images
author: HONGMING XU
CCF
qeutions: mxu@ualberta.ca
'''
import os
import numpy as np
import openslide
import scipy
import time
import matplotlib.pyplot as plt
from PIL import Image
import concurrent.futures
from itertools import repeat
from tqdm import tqdm

def wsi_coarse_level(Slide,Magnification,Stride,tol=0.02):
    # get slide dimensions, zoom levels, and objective information
    Factors = Slide.level_downsamples
    Objective = float(Slide.properties[
                          openslide.PROPERTY_NAME_OBJECTIVE_POWER])

    # determine if desired magnification is avilable in file
    Available = tuple(Objective / x for x in Factors)
    Mismatch = tuple(x - Magnification for x in Available)
    AbsMismatch = tuple(abs(x) for x in Mismatch)
    if min(AbsMismatch) <= tol:
        Level = int(AbsMismatch.index(min(AbsMismatch)))
        Factor = 1
    else:
        if min(Mismatch) < 0:  # determine is there is magnifications below 2.5x
            # pick next lower level, upsample
            Level = int(min([i for (i, val) in enumerate(Mismatch) if val < 0]))
        else:
            # pick next higher level, downsample
            Level = int(max([i for (i, val) in enumerate(Mismatch) if val > 0]))

        Factor = Magnification / Available[Level]

    # translate parameters of input tiling schedule into new schedule
    Tout = [round(Stride[0]*Magnification/Objective), round(Stride[0]*Magnification/Objective)]


    return Level,Tout,Factor

def parallel_tiling(i,X,Y,dest_imagePath,img_name,Stride,File):
    Slide = openslide.OpenSlide(File)

    for j in range(X.shape[1] - 1):
        Tile = Slide.read_region((int(X[i, j]), int(Y[i, j])), 0, (Stride[0], Stride[1]))
        Tile = np.asarray(Tile)
        Tile = Tile[:, :, :3]
        bn = np.sum(Tile[:, :, 0] < 5) + np.sum(np.mean(Tile,axis=2) > 245)
        if (np.std(Tile[:, :, 0]) + np.std(Tile[:, :, 1]) + np.std(Tile[:, :, 2])) / 3 > 18 and bn < Stride[0] * Stride[
            1] * 0.3:
            tile_name = img_name.split('.')[0] + '_' + str(X[i, j]) + '_' + str(Y[i, j]) + '_' + str(
                Stride[0]) + '_' + str(Stride[1]) + '_' + '.png'
            img = Image.fromarray(Tile)
            img.save(dest_imagePath + tile_name)

            # for debug
            # if debug_g==True:
            #     pred_gg[i,j]=255

def wsi_tiling(File,dest_imagePath,img_name,Tile_size,debug=False,parallel_running=True):
    since = time.time()
    # open image
    Slide = openslide.OpenSlide(File)

    xr = float(Slide.properties['openslide.mpp-x'])  # pixel resolution at x direction
    yr = float(Slide.properties['openslide.mpp-y'])  # pixel resolution at y direction
    # generate X, Y coordinates for tiling
    Stride = [round(Tile_size[0] / xr), round(Tile_size[1] / yr)]
    Dims = Slide.level_dimensions
    X = np.arange(0, Dims[0][0] + 1, Stride[0])
    Y = np.arange(0, Dims[0][1] + 1, Stride[1])
    X, Y = np.meshgrid(X, Y)

    # MappingMag=2.5
    # Level, Tout, Factor = wsi_coarse_level(Slide, MappingMag, Stride)
    #
    # # get width, height of image at low-res reading magnification
    # lrHeight = Slide.level_dimensions[Level][1]
    # lrWidth = Slide.level_dimensions[Level][0]
    #
    # # read in whole slide at low magnification
    # LR = Slide.read_region((0, 0), Level, (lrWidth, lrHeight))
    #
    # # convert to numpy array and strip alpha channel
    # LR = np.asarray(LR)
    # LR = LR[:, :, :3]
    if debug==True:
        pred_g = np.zeros((X.shape[0] - 1, X.shape[1] - 1, 3), 'uint8')
        global pred_gg
        pred_gg=pred_g

        global debug_g
        debug_g=debug

    if parallel_running==True:
        # parallel-running
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
             for _ in executor.map(parallel_tiling, list(range(X.shape[0]-1)), repeat(X), repeat(Y), repeat(dest_imagePath),repeat(img_name),repeat(Stride),repeat(File)):
                 pass
    else: # for debug
        for i in range(150,X.shape[0] - 1):
            for j in range(X.shape[1] - 1):
                    Tile = Slide.read_region((int(X[i, j]), int(Y[i, j])), 0, (Stride[0], Stride[1]))
                    Tile = np.asarray(Tile)
                    Tile = Tile[:, :, :3]
                    bn=np.sum(Tile[:, :, 0] < 5) + np.sum(np.mean(Tile,axis=2) > 245)
                    if (np.std(Tile[:,:,0])+np.std(Tile[:,:,1])+np.std(Tile[:,:,2]))/3>18 and bn<Stride[0]*Stride[1]*0.3:
                        tile_name=img_name.split('.')[0]+'_'+str(X[i,j])+'_'+str(Y[i,j])+'_'+str(Stride[0])+'_'+str(Stride[1])+'_'+'.png'
                        img = Image.fromarray(Tile)
                        img.save(dest_imagePath+tile_name)

    time_elapsed = time.time() - since
    print('Training complete in {:.0f}m {:.0f}s'.format(
        time_elapsed // 60, time_elapsed % 60))

if __name__=='__main__':

    kang_colon_slide=False
    lee_gastric_slide=False
    tcga_coad_read_slide=True
    ## to tiling yonsei data
    if kang_colon_slide==True:
        imagePath=['../../data/kang_colon_slide/181119/',
                   '../../data/kang_colon_slide/181211/',
                   '../../data/kang_colon_slide/Kang_MSI_WSI_2019_10_07/']

        destPath=['../../data/pan_cancer_tils/data_yonsei_v01/181119_v2/',
                  '../../data/pan_cancer_tils/data_yonsei_v01/181211_v2/',
                  '../../data/pan_cancer_tils/data_yonsei_v01/Kang_MSI_WSI_2019_10_07_v2/']

        wsi_ext='.mrxs'
    elif lee_gastric_slide == True:  ## to tiling lee data
        imagePath = ['../../data/lee_gastric_slide/Stomach_Immunotherapy/']
        destPath = ['../../data/pan_cancer_tils/data_lee_gastric/']
        wsi_ext='.tiff'
    elif tcga_coad_read_slide==True:
        imagePath = ['../../data/tcga_coad_slide/tcga_coad/quality_a1/',
                     '../../data/tcga_coad_slide/tcga_coad/quality_a2/',
                     '../../data/tcga_coad_slide/tcga_coad/quality_b/',
                     '../../data/tcga_coad_slide/tcga_coad/quality_uncertain/',
                     '../../data/tcga_read_slide/dataset/']
        destPath = ['../../data/tcga_coad_read_data/coad_read_tissue_tiles/tcga_coad_a1/',
                    '../../data/tcga_coad_read_data/coad_read_tissue_tiles/tcga_coad_a2/',
                    '../../data/tcga_coad_read_data/coad_read_tissue_tiles/tcga_coad_b/',
                    '../../data/tcga_coad_read_data/coad_read_tissue_tiles/tcga_coad_uncertain/',
                    '../../data/tcga_coad_read_data/coad_read_tissue_tiles/tcga_read/']
        wsi_ext='.svs'

    else:
        raise ValueError('incorrect data selection~~~~~~')

    # tileSize=[50,50] # micro-meters
    tileSize = [112, 112]  # micro-meters
    for i in range(4,len(imagePath)):
        temp_imagePath = imagePath[i]
        dest_imagePath = destPath[i]
        wsis = sorted(os.listdir(temp_imagePath))
        for img_name in tqdm(wsis[27:]):
            if wsi_ext in img_name:
                file = temp_imagePath + img_name
                wsi_tiling(file, dest_imagePath, img_name, tileSize)