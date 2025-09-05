import sqlalchemy
import secrets
import datetime
from video_object_detection import connections

# sql alchemy ORM engine creation
engine = sqlalchemy.create_engine(connections.sql_connection_string)  # Ubuntu server connection string
metadata_obj = sqlalchemy.MetaData()
metadata_obj.reflect(engine)  # metadata is container object, reflects existing tables to populate metadata
users, movies, frames = metadata_obj.tables['Users'], metadata_obj.tables['Movies'], metadata_obj.tables['Frames']
searches, results = metadata_obj.tables['Searches'], metadata_obj.tables['Results']
connection = engine.connect()

# SQL alchemy query functions


def get_user_id(email):
    statement = sqlalchemy.select(users.c.UserId).where(users.c.Email == email)
    res = connection.execute(statement).fetchall()
    return res[0][0] if len(res) > 0 else None


def get_api_key(uid):
    statement = sqlalchemy.select(users.c.APIKey).where(users.c.UserId == uid)
    res = connection.execute(statement).fetchall()
    return res[0][0]


def get_movie_id(uid, name):
    statement = sqlalchemy.select(movies.c.MovieId).where(movies.c.UserId == uid, movies.c.Name == name)
    res = connection.execute(statement).fetchall()
    return res[0][0] if len(res) > 0 else None


def add_user(first, last, email):
    key = secrets.token_hex(32)  # 32 byte API key
    statement = sqlalchemy.insert(users).values(FirstName=first, LastName=last, Email=email, APIKey=key)
    connection.execute(statement)
    connection.commit()
    return key


def add_movie(uid, name):
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # small date time rounds to nearest minute
    statement = sqlalchemy.insert(movies).values(UserId=uid, Name=name, UploadDate=dt)
    connection.execute(statement)
    connection.commit()


def update_upload(mid, status):
    statement = sqlalchemy.update(movies).where(movies.c.MovieId == mid).values(UploadStatus=status)
    connection.execute(statement)
    connection.commit()


def get_uploads(uid):
    statement = sqlalchemy.select(movies.c.Name, movies.c.UploadStatus).where(movies.c.UserId == uid)
    res = connection.execute(statement).fetchall()
    for i in range(len(res)):
        res[i] = tuple(res[i])  # caste to tuple for sqlalchemy engine type
    return res if len(res) > 0 else None


def get_upload_status(mid):
    statement = sqlalchemy.select(movies.c.UploadStatus).where(movies.c.MovieId == mid)
    res = connection.execute(statement).fetchall()
    return res[0][0] if len(res) > 0 else None


def add_frame(mid, num):
    print(f'add {mid} {num}')
    statement = sqlalchemy.insert(frames).values(MovieId=mid, FrameNumber=num)
    connection.execute(statement)
    connection.commit()


def add_search(mid, word):
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # small date time rounds to nearest minute
    statement = sqlalchemy.insert(searches).values(MovieId=mid, SearchWord=word, SearchDate=dt, SearchStatus=0)
    connection.execute(statement)
    connection.commit()


def get_search_id(mid, word):
    statement = sqlalchemy.select(searches.c.SearchId).where(searches.c.MovieId == mid, searches.c.SearchWord == word)
    res = connection.execute(statement).fetchall()
    return res[0][0] if len(res) > 0 else None


def add_result(sid, url):
    statement = sqlalchemy.insert(results).values(SearchId=sid, URL=url)
    connection.execute(statement)
    connection.commit()


def update_search(sid, status):
    statement = sqlalchemy.update(searches).where(searches.c.SearchId == sid).values(SearchStatus=status)
    connection.execute(statement)
    connection.commit()


def search_status(sid):
    statement = sqlalchemy.select(searches.c.SearchStatus).where(searches.c.SearchId == sid)
    res = connection.execute(statement).fetchall()
    return res[0][0] if len(res) > 0 else None


def get_results(sid):  # returns all searches if no sid is provided

    statement = sqlalchemy.select(results.c.URL).where(results.c.SearchId == sid)
    res = connection.execute(statement).fetchall()
    for i in range(len(res)):
        res[i] = tuple(res[i])
    return res if len(res) > 0 else None


def get_searches(uid):
    statement = sqlalchemy.select(movies.c.Name,
                                  searches.c.SearchWord,
                                  searches.c.SearchDate,
                                  searches.c.SearchStatus).join(movies).where(movies.c.UserId == uid)
    temp_res = connection.execute(statement).fetchall()
    res = []
    for name, word, date, status in temp_res:
        res.append([name, word, str(date), status])
    return res


def delete_search(sid):  # statements must be executed separately
    statements = [sqlalchemy.delete(results).where(results.c.SearchId == sid),
                  sqlalchemy.delete(searches).where(searches.c.SearchId == sid)]
    for s in statements:
        connection.execute(s)
    connection.commit()


def delete_movie(mid):  # delete all searches and results before deleting movie
    statement = sqlalchemy.select(searches.c.SearchId).where(searches.c.MovieId == mid)
    res = connection.execute(statement).fetchall()
    for search in res:
        delete_search(search[0])
    # delete movie and frames
    statements = [sqlalchemy.delete(frames).where(frames.c.MovieId == mid),
                  sqlalchemy.delete(movies).where(movies.c.MovieId == mid)]
    for s in statements:
        connection.execute(s)
    connection.commit()


def delete_frames(mid):
    statement = sqlalchemy.delete(frames).where(frames.c.MovieId == mid)
    connection.execute(statement)
    connection.commit()


def delete_results(sid):
    statement = sqlalchemy.delete(results).where(results.c.ResultId == sid)
    connection.execute(statement)
    connection.commit()
