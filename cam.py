import cv2
import time
import imutils
import numpy as np
s
cam = cv2.VideoCapture(0)
time.sleep(1)

firstFrame = None
area = 500

alpha = 0.5

while True:
    _, img = cam.read()
    if img is None:
        break
    
    text = "Normal"
    grayImg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    grayImg = cv2.GaussianBlur(grayImg, (21, 21), 0)
    
    if firstFrame is None:
        firstFrame = grayImg.astype("float")
        continue

    # Dynamic background subtraction
    cv2.accumulateWeighted(grayImg, firstFrame, alpha)
    imgDiff = cv2.absdiff(grayImg, cv2.convertScaleAbs(firstFrame))
    threshImg = cv2.threshold(imgDiff, 25, 255, cv2.THRESH_BINARY)[1]
    threshImg = cv2.dilate(threshImg, None, iterations=2)
    
    # Contour detection
    cnts = cv2.findContours(threshImg.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    for c in cnts:
        if cv2.contourArea(c) < area:
            continue
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = "Moving Object detected"
    
    cv2.putText(img, text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.imshow("Camera Feed", img)
    
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cam.release()
cv2.destroyAllWindows()
