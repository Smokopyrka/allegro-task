from flask import Flask, abort
from logic import API, InvalidUserError, UserQuotaExceededError

app = Flask(__name__)
api = API()


@app.errorhandler(InvalidUserError)
def handle_invalid_user(e):
    print(e)
    return ('<h1>Invalid User</h1>'
            '<p>Requested user doesn\'t exist</p>', 404)


@app.errorhandler(UserQuotaExceededError)
def handle_exceeded_user_quota(e):
    print(e)
    return ('<h1>User Quota Exceeded</h1>'
            '<p>User hourly request quota exceeded</p>', 403)


@app.get('/user/<username>/repos')
async def get_user_repos(username):
    data = [repo async for repo in api.get_user_repos(username)]
    return {
        'data': data
    }


@app.get('/user/<username>/stars')
async def get_user_star_sum(username):
    return {
        'star_total': await api.get_user_star_total(username)
    }


@app.get('/user/<username>/languages')
async def get_user_languages(username):
    return {
        'data': await api.get_users_language_list(username)
    }
