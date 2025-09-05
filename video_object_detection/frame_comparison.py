import cv2

# compares two images using ORB FLANN based matching and Lowe's ratio
# if the images are sufficiently different returns True, else False


def dif_frame(i1, i2):  # accepts numpy.ndarray files
    i1, i2 = cv2.cvtColor(i1, 0), cv2.cvtColor(i2, 0)  # convert to grayscale
    # don't use imread, it is platform specific and can return dif grayscale values
    # 5 ORB threshold for both edge and fast has the best performance with no errors
    orb = cv2.ORB_create(edgeThreshold=5, fastThreshold=5)  # too high of thresholds throw 215 error
    kp1, des1 = orb.detectAndCompute(i1, None)  # second arg is the mask, has to be included as None
    kp2, des2 = orb.detectAndCompute(i2, None)

    flann_index_lsh = 6  # flann matcher setup
    index_params = dict(algorithm=flann_index_lsh,
                        table_number=6,  # 12, default values per documentation
                        key_size=12,  # 20
                        multi_probe_level=1)  # 2
    flann_matcher = cv2.FlannBasedMatcher(index_params, {})  # empy dict for search params
    knn = flann_matcher.knnMatch(des1, des2, k=2)  # returns each point's 2 nearest neighbors for Lowe's ratio

    matches = 0
    ratio_threshold = .7 # Lowe's threshold ratio, .7 best combination of performance and accuracy
    match_threshold = 30 # current threshold for the same image is 30 matches
    for points in knn:  # Lowe's ratio, check if at least two nearest neighbors, unmatched desc return single object
        if len(points) == 2 and points[0].distance < ratio_threshold * points[1].distance:
            matches += 1
        if matches == match_threshold:
            return False
    return True
