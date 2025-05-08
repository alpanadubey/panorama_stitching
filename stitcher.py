import cv2
import numpy as np

def crop_black(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        x, y, w, h = cv2.boundingRect(contours[0])
        return image[y:y+h, x:x+w]
    return image

def detect_and_match(img1, img2, descriptor_type='sift'):
    if descriptor_type == 'sift':
        feature = cv2.SIFT_create()
        matcher = cv2.BFMatcher()
    elif descriptor_type == 'orb':
        feature = cv2.ORB_create()
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    else:
        raise ValueError("Invalid descriptor")

    kp1, des1 = feature.detectAndCompute(img1, None)
    kp2, des2 = feature.detectAndCompute(img2, None)

    matches = matcher.knnMatch(des1, des2, k=2)
    good = [m for m, n in matches if m.distance < 0.75 * n.distance]

    matched_img = cv2.drawMatches(img1, kp1, img2, kp2, good, None,
                                  flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    cv2.imwrite('static/matched.jpg', matched_img)

    return kp1, kp2, good

def stitch_images(img1, img2, descriptor_type='sift'):
    kp1, kp2, good_matches = detect_and_match(img1, img2, descriptor_type)

    if len(good_matches) < 4:
        raise Exception("Not enough matches found.")

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    result = cv2.warpPerspective(img1, H, (img1.shape[1] + img2.shape[1], img1.shape[0]))
    result[0:img2.shape[0], 0:img2.shape[1]] = img2

    return crop_black(result)
