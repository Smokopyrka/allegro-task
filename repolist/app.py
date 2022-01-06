import os

from flask import Flask, abort, jsonify

from logic import API, InvalidUserError, UserQuotaExceededError

app = Flask(__name__)

auth_token = os.environ.get('GITHUB_TOKEN')
username = os.environ.get('GITHUB_USER')
url = 'https://api.github.com'
api = API(url, auth_token=auth_token, username=username)


@app.errorhandler(InvalidUserError)
def handle_invalid_user(e):
    print(e)
    return ({
        'message': 'User not found'
    }, 404)


@app.errorhandler(UserQuotaExceededError)
def handle_exceeded_user_quota(e):
    print(e)
    return ({
        'message': 'User quota exceeded'
    }, 403)


@app.get('/user/<username>/repos')
async def get_user_repos(username):
    data = [repo async for repo in api.get_user_repos(username)]
    return jsonify(data)


@app.get('/user/<username>/stars')
async def get_user_star_sum(username):
    return {
        'star_count': await api.get_user_star_total(username)
    }


@app.get('/user/<username>/languages')
async def get_user_languages(username):
    data = await api.get_users_language_list(username)
    return jsonify(data)
