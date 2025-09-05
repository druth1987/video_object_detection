import flask
import flask_cors
from celery import Celery
from video_object_detection import s3_api
from video_object_detection import sql_alchemy_queries
from video_object_detection import celery_tasks
from video_object_detection import connections

# Flask WSGI server API with CORS open to 127.0.0.1 for front end testing
flask_api = flask.Flask(__name__)
flask_cors.CORS(flask_api, origins=["http://127.0.0.1"])  # allows front end requests from entered IP through CORS

# celery client app constructor for async server calls
cel_app = Celery('cel_app', broker=connections.redis_url, backend=connections.redis_url, task_ignore_result=True)
cel_app.set_default()  # set default to access shared tasks


@flask_api.route('/users', methods=['POST'])
def users():  # params: email,first,last
    data = flask.request.get_json()

    # validation and error handling
    if 'email' not in data or 'first' not in data or 'last' not in data:
        return 'Error: Missing Required Parameters', 400
    if sql_alchemy_queries.get_user_id(data['email']):
        return 'Error: Email Already In Use', 400

    key = sql_alchemy_queries.add_user(data['first'], data['last'], data['email'])
    return f'User Added, Your API Key Is: {key}', 201  # client response, http status response code


@flask_api.route('/uploads', methods=['POST', 'GET'])  # need file authentication
def uploads():  # two part file upload, form data: name, file

    if flask.request.method == 'POST':  # params: email, name, movie
        # get and validate form data
        keys = flask.request.form.keys()
        files = flask.request.files.keys()

        if 'email' not in keys or 'name' not in keys or 'movie' not in files:
            return 'Error: Missing Required Parameters', 400

        email = flask.request.form.get('email')
        name = flask.request.form.get('name')
        mov = flask.request.files['movie']

        # if multiple files uploaded, only checks/processes the first one
        if mov.mimetype != 'video/mp4':
            return 'Error: Upload Must Be MP4 File'

        uid = sql_alchemy_queries.get_user_id(email)

        if not uid:
            return 'Error: Email Does Not Exist', 400
        if flask.request.headers.get('API-Key') != sql_alchemy_queries.get_api_key(uid):
            return 'Invalid API Key', 401

        # check if movie failed to upload previously, and is still in SQL to prevent duplicate error
        mid = sql_alchemy_queries.get_movie_id(uid, name)
        mov_status = sql_alchemy_queries.get_upload_status(mid)

        if mid:  # SQL movie status of 0 == upload error
            if mov_status != 0:
                return 'Error: Movie Already Exists', 400
            sql_alchemy_queries.update_upload(mid, None)  # reset failed movie upload status to processing
        else:
            sql_alchemy_queries.add_movie(uid, name)
            mid = sql_alchemy_queries.get_movie_id(uid, name)

        # save, parse/upload frames, delete
        mov.save(f'video_saves/{uid}-{mid}.mp4')
        celery_tasks.process_mov.delay(uid, mid)  # have to use delay to call celery tasks
        return 'Movie Uploading', 202

    else:  # GET params: email, name
        data = flask.request.args
        if 'email' not in data.keys():
            return 'Error: Missing Required Parameters', 400
        uid = sql_alchemy_queries.get_user_id(data['email'])
        if not uid:
            return 'Error: Email Does Not Exist', 400
        if flask.request.headers.get('API-Key') != sql_alchemy_queries.get_api_key(uid):
            return 'Invalid API Key', 401
        upload_list = sql_alchemy_queries.get_uploads(uid)
        if not upload_list:
            return 'No Uploads Found For User', 400
        return upload_list, 200  # returns null for in process


@flask_api.route('/movies', methods=['GET', 'DELETE'])
def movies():  # params: email,name
    data = flask.request.args
    if 'email' not in data.keys() or 'name' not in data.keys():
        return 'Error: Missing Required Parameters', 400

    uid = sql_alchemy_queries.get_user_id(data['email'])
    if not uid:
        return 'Error: Email Does Not Exist', 400
    if flask.request.headers.get('API-Key') != sql_alchemy_queries.get_api_key(uid):
        return 'Invalid API Key', 401
    mid = sql_alchemy_queries.get_movie_id(uid, data['name'])
    if not mid:
        return 'Error: Movie Does Not Exist', 400

    # error check
    up_status = sql_alchemy_queries.get_upload_status(mid)
    if up_status == 0:
        return 'Error: Movie Failed to Upload', 400

    if flask.request.method == 'GET':  # params: email, name
        frames = s3_api.get_frame_urls(uid, mid)
        return frames, 200

    else:  # DELETE params: email,name
        s3_api.delete_movie(uid, mid)
        sql_alchemy_queries.delete_movie(mid)
        return 'Movie and Any Corresponding Searches Deleted', 200


@flask_api.route('/searches', methods=['GET', 'POST', 'DELETE'])
def searches():
    if flask.request.method == 'POST':  # params: email, name, word
        data = flask.request.get_json()

        # validation and error handling
        if 'email' not in data or 'name' not in data or 'word' not in data:
            return 'Error: Missing Required Parameters', 400
        uid = sql_alchemy_queries.get_user_id(data['email'])
        if not uid:
            return 'Error: Email Does Not Exist', 400
        if flask.request.headers.get('API-Key') != sql_alchemy_queries.get_api_key(uid):
            return 'Invalid API Key', 401
        mid = sql_alchemy_queries.get_movie_id(uid, data['name'])
        if not mid:
            return 'Error: Movie Does Not Exist', 400

        # check if search failed previously, and is still in SQL to prevent duplicate error
        sid = sql_alchemy_queries.get_search_id(mid, data['word'])
        search_status = sql_alchemy_queries.search_status(sid)

        if sid:  # SQL search status of 0 == upload error
            if search_status != 0:
                return 'Error: Search Already Exists', 400
            sql_alchemy_queries.update_search(sid, None)  # reset failed search status to processing
        else:
            sql_alchemy_queries.add_search(mid, data['word'])
            sid = sql_alchemy_queries.get_search_id(mid, data['word'])

        celery_tasks.search_mov.delay(sid, uid, mid, data['word'])
        return 'Searching Movie', 202

    else:  # GET and DELETE
        # validation
        data = flask.request.args
        if 'email' not in data.keys() or 'name' not in data.keys():
            return 'Error: Missing Required Parameters', 400
        uid = sql_alchemy_queries.get_user_id(data['email'])
        if not uid:
            return 'Error: Email Does Not Exist', 400
        if flask.request.headers.get('API-Key') != sql_alchemy_queries.get_api_key(uid):
            return 'Invalid API Key', 401
        mid = sql_alchemy_queries.get_movie_id(uid, data['name'])
        if not mid:
            return 'Error: Movie Does Not Exist', 400

        # if no search word returns status of all searches for movie
        if flask.request.method == 'GET':  # params: email, name, *word
            if 'word' in data.keys():
                sid = sql_alchemy_queries.get_search_id(mid, data['word'])
                if not sid:
                    return 'Error: Search Does Not Exist', 400

                # check for failed/still processing searches
                search_status = sql_alchemy_queries.search_status(sid)
                if search_status == 0:  # error check
                    return 'Search Failed to Complete', 400
                elif search_status != 1:  # avoid None equality comparison
                    return 'Search Still in Progress', 400

                res = sql_alchemy_queries.get_results(sid)
                if not res:
                    return 'Search Did Not Find Any Results', 400
                return res
            res = sql_alchemy_queries.get_searches(uid)  # if no search word, gets all searches for that movie only
            return res, 200

        else:  # delete params: email,name,word
            sid = sql_alchemy_queries.get_search_id(mid, data['word'])
            if not sid:
                return 'Error: Search Does Not Exist', 400
            if sql_alchemy_queries.search_status(sid) == 0:
                return 'Error: Search Failed to Complete', 400
            sql_alchemy_queries.delete_search(sid)
            return 'Search Deleted', 200


if __name__ == "__main__":
    flask_api.run()  # Threaded = true arg enables threading


