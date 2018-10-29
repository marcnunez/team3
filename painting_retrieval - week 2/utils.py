import pickle
import os
import cv2
from matplotlib import pyplot as plt
import numpy as np

def list_ds(path_images):
    listImages =[]
    # Import Data from directories
    for filename in os.listdir(path_images):
        if filename.endswith(".jpg"):
            listImages.append(filename)
    return listImages

def create_dir(pathSave):
    if not os.path.exists(pathSave):
        os.makedirs(pathSave)
		
def get_gray_image(im, path):
    imBGR = cv2.imread(path+im)
    return cv2.cvtColor(imBGR, cv2.COLOR_BGR2GRAY)

def get_bgr_image(im, path):
    imBGR = cv2.imread(path+im)
    return imBGR

def plot_gray(im):
    plt.imshow(im, cmap='gray')
    plt.show()

def plot_rgb(im):
    plt.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
    plt.show()

def plot_sift(sift, path):
    imName, kps, descs = sift    
    imGray = get_gray_image(imName, path)
    imSift = cv2.drawKeypoints(imGray, kps, None)
    plot_rgb(imSift)  

def plot_matches(siftA, siftB, pathA, pathB, matches):
    imNameA, kpsA, descsA = siftA    
    imNameB, kpsB, descsB = siftB  
    imA = get_bgr_image(imNameA, pathA)
    imB = get_bgr_image(imNameB, pathB)
    match_img = cv2.drawMatches(
        imA, kpsA,
        imB, kpsB,
        matches, imB.copy(), flags=0)
    plt.figure(figsize=(12,6))
    plt.imshow(match_img)
    plot_rgb(match_img)    
    
def save_pkl(list_of_list, path):
    create_dir(path)
    with open(path+'result.pkl', 'wb') as f:
        pickle.dump(list_of_list, f)

def submission_list(df):
    project_result = []
    for query in df.Query.unique():
        dfQuery = df[df.Query == query]
        query_result = []
        for i in range(len(dfQuery)):
            dfImg = dfQuery[dfQuery.Order == i]
            query_result.append(dfImg['Image'].values[0])
        project_result.append(query_result.copy())
    return project_result

## Average precision at K calculation
def apk(actual, predicted, k=10):
    """
    Computes the average precision at k.

    This function computes the average prescision at k between two lists of
    items.

    Parameters
    ----------
    actual : list
             A list of elements that are to be predicted (order doesn't matter)
    predicted : list
                A list of predicted elements (order does matter)
    k : int, optional
        The maximum number of predicted elements

    Returns
    -------
    score : double
            The average precision at k over the input lists

    """
    if len(predicted)>k:
        predicted = predicted[:k]

    score = 0.0
    num_hits = 0.0

    for i,p in enumerate(predicted):
        if p in actual and p not in predicted[:i]:
            num_hits += 1.0
            score += num_hits / (i+1.0)

    if not actual:
        return 0.0
    
    result = score / min(len(actual), k)
#    print('APK:', result)
    return result

## Mean average precision at K calculation
def mapk(actual, predicted, k=10):
    """
    Computes the mean average precision at k.

    This function computes the mean average prescision at k between two lists
    of lists of items.

    Parameters
    ----------
    actual : list
             A list of lists of elements that are to be predicted
             (order doesn't matter in the lists)
    predicted : list
                A list of lists of predicted elements
                (order matters in the lists)
    k : int, optional
        The maximum number of predicted elements

    Returns
    -------
    score : double
            The mean average precision at k over the input lists

    """
    return np.mean([apk(a,p,k) for a,p in zip(actual, predicted)])

def get_query_gt(pkl_fle):
    resultList = []
    with open(pkl_fle, 'rb') as f:
        data = pickle.load(f)    
    for key in data:
        resultList.append(['ima_{:06d}.jpg'.format(data[key])])
    return resultList