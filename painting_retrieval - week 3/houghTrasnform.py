import cv2
import numpy as np
import matplotlib.pyplot as plt
from utils import get_gray_image, list_ds
from scipy.spatial import distance as dist
from resizeImage import image_save_original_sizes

def getSizeSquare(points):
    x1, y1 = points[0]
    x2, y2 = points[3]
    x3, y3 = points[1]
    
    height = int(round(np.sqrt((x1-x2)**2 + (y1-y2)**2)))
    width = int(round(np.sqrt((x1-x3)**2 + (y1-y3)**2))) 
    return height, width


def cropAndRotate(img, points):
    height, width = getSizeSquare(points)
    
    pts1 = np.float32([points[0], points[1], points[2], points[3]])
    pts2 = np.float32([[0,0], [width,0], [width, height],[0,height]])
    M = cv2.getPerspectiveTransform(pts1,pts2)
    dst = cv2.warpPerspective(img,M,(width,height))
    
    plt.subplot(121),plt.imshow(img),plt.title('Input')
    plt.subplot(122),plt.imshow(dst),plt.title('Output')
    plt.show()

def groupLines(lines):
    groupedLines = []
    result = []

    if lines is not None:
        for line in lines:
            for rho,theta in line:
                if len(groupedLines)>0:
                    controlerModifier = False
                    for group in groupedLines:
                        inc = 0.05
                        if(theta+inc>group[2] and theta-inc<group[2]):
                            controlerModifier = True
                            if (rho<group[0]):
                                group[0]=rho
                            elif ( rho> group[1]):
                                group[1]=rho
                                    
                            group[3] = group[3] + 1
                            
                            group[2] = (group[2] * group[3] + theta)/(group[3]+1)
                                     
                    if (controlerModifier == False):
                        groupedLines.append([rho, rho, theta,1])
                else:
                    groupedLines.append([rho, rho, theta,1])
    groupedLines= sorted(groupedLines, key = lambda x: x[3])   
    groupedLines.reverse()
    result.append(groupedLines.pop(0))
    mainTheta = result[0][2]
    for group in groupedLines:  
        complementTheta = group[2]
        angle = abs(mainTheta - complementTheta)
        if(angle>1.4 and angle<1.75):
            result.append(group)
            break           
    paintingTheta = 0
    # rad to degrees
    angles = [int(mainTheta*180/np.pi), int(complementTheta*180/np.pi)]
    angles = sorted(angles)  
    # get angle closer to 0º/180º
    if(abs(angles[0]-90) > abs(angles[1]-90)):
        paintingTheta = 180-angles[0]
    else:
        paintingTheta = 180-angles[1]
        
    return result, paintingTheta

def intersection(line1, line2):
    points = []
    theta1 = line1[2]
    theta2 = line2[2]
    for i in range(0,2):
        for j in range(0,2):
            A = np.array([
                [np.cos(theta1), np.sin(theta1)],
                [np.cos(theta2), np.sin(theta2)]
            ])
            b = np.array([[line1[i]], [line2[j]]])
            x0, y0 = np.linalg.solve(A, b)
            x0, y0 = int(np.round(x0)), int(np.round(y0))
            points.append([x0,y0])
    return points

def order_points(pts):
	xSorted = pts[np.argsort(pts[:, 0]), :]
	leftMost = xSorted[:2, :]
	rightMost = xSorted[2:, :]
	leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
	(tl, bl) = leftMost
 
	D = dist.cdist(tl[np.newaxis], rightMost, "euclidean")[0]
	(br, tr) = rightMost[np.argsort(D)[::-1], :]
 
	return np.array([tl, tr, br, bl], dtype="float32")

def houghTrasnformGrouped(img, percent_h, percent_w, imgOrig):
    edges = auto_canny(img)
    plt.imshow(edges)
    plt.show()
    lines = cv2.HoughLines(edges, 1, np.pi/180, 30, None, 0, 0)
    groupedLines, paintingTheta = groupLines(lines)
    if len(groupedLines)>1:
        pack1 = groupedLines[0]
        pack2 = groupedLines[1]
        
        points = intersection(pack1, pack2)
        points = np.array(points)
        points = order_points(points)
        cropAndRotate(img, points)
        for point in points:
            img = cv2.circle(img,(point[0],point[1]), 5, (0,0,255), -1)
            
        for j in range(0,2):
            pack = groupedLines[j]
            theta = pack[2]
            a = np.cos(theta)
            b = np.sin(theta)
            for i in range(0,2):
                x0 = a*pack[i]
                y0 = b*pack[i]
                x1 = int(x0 + 1000*(-b))
                y1 = int(y0 + 1000*(a))
                x2 = int(x0 - 1000*(-b))
                y2 = int(y0 - 1000*(a))
                img = cv2.line(img,(x1,y1),(x2,y2),(0,0,255),2)

    plt.imshow(img)
    plt.show()
    
    points = points * percent_h
    points = np.floor(points)
    points = points.astype(int)
    
    for point in points:
        imgOrig = cv2.circle(imgOrig,(point[0],point[1]), 20, (0,0,255), -1)
    plt.imshow(imgOrig)
    plt.show()
    
    return [paintingTheta, points.tolist()]
    
def auto_canny(image, sigma=0.33):
	# compute the median of the single channel pixel intensities
	v = np.median(image)
 
	# apply automatic Canny edge detection using the computed median
	lower = int(max(0, (1.0 - sigma) * v))
	upper = int(min(255, (1.0 + sigma) * v))
	edged = cv2.Canny(image, lower, upper)
 
	# return the edged image
	return edged   


def compute_hough(path, resize):
    im_list = list_ds(path)
    result = []
    for imName in im_list:
        imgOrig = get_gray_image(imName, path)
        image = get_gray_image(imName, path, resize, 256)
        percent_w, percent_h = image_save_original_sizes(imgOrig, image)
        result.append(houghTrasnformGrouped(image, percent_h, percent_w, imgOrig))
    return result
    
if __name__ == "__main__":
    pathQuery = "dataset/"
    result = compute_hough(pathQuery, True)