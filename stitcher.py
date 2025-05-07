import cv2
import numpy as np

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

    kp_img1 = cv2.drawKeypoints(img1, kp1, None, flags=cv2.DrawMatchesFlags_DRAW_RICH_KEYPOINTS)
    kp_img2 = cv2.drawKeypoints(img2, kp2, None, flags=cv2.DrawMatchesFlags_DRAW_RICH_KEYPOINTS)

    matches = matcher.knnMatch(des1, des2, k=2)
    good = [m for m, n in matches if m.distance < 0.75 * n.distance]

    matched_img = cv2.drawMatches(img1, kp1, img2, kp2, good, None,
                                  flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

    return kp1, kp2, good, matched_img

def stitch_images(img1, img2, descriptor_type='sift'):
    kp1, kp2, good_matches, match_img = detect_and_match(img1, img2, descriptor_type)

    if len(good_matches) < 4:
        raise Exception("Not enough matches")

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1,1,2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1,1,2)

    H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    stitched = cv2.warpPerspective(img1, H, (img2.shape[1] + img1.shape[1], img2.shape[0]))
    stitched[0:img2.shape[0], 0:img2.shape[1]] = img2

    cv2.imwrite('static/matched.jpg', match_img)
    stitched = crop_black(stitched)

    return stitched

def crop_black(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        x, y, w, h = cv2.boundingRect(contours[0])
        cropped = image[y:y+h, x:x+w]
        return cropped
    return image
