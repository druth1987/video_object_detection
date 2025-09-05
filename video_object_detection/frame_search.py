from transformers import pipeline

# called by Celery asynchronous task queue on Ubuntu application server
# uses OWLv2 model to perform zero shot object detection on each distinct frame from the video


def frame_search(images, search_word): # accepts s3 urls and user inputted search word
    checkpoint = "google/owlv2-base-patch16-ensemble"  # current model
    detector = pipeline(model=checkpoint, task="zero-shot-object-detection", device=0)  # device = cuda gpu integration

    res = []
    match_threshold = .2  # image match threshold, .2 appears accurate without misidentification
    for url in images:  # detector can accept urls directly
        predictions = detector(url, search_word)  # default threshold is .1, sorted by highest rank
        if len(predictions) == 0 or predictions[0]['score'] < match_threshold:
            continue
        res.append(url)
    return res
