# Dominik Lapinski - Zadanie nr.3 (Software Engineer)

## Table of Contents
* [General Info](#general-info)
* [Setup](#setup)
* [API Endpoints](#api-endpoints)
* [Technologies](#technologies)
* [Notes](#notes)
* [Improvement Ideas](#improvement-ideas)

## General Info
Simple REST API written in Flask that can:
* List all repos along with their star counts for a given user.
* Get the sum of star counts of all repos for a given user.
* Get the list of all languages the repos of a given user are written in, along with the number of bytes that have been written in each of them, ranked from the most used language to the least used language by byte count.

## Setup

### Running the application
Make sure you have all the dependencies installed. To do so, execute the command `pip3 install -r requirements.txt` in the root directory of the project. To run the application, declare an environment variable `FLASK_APP` and set it to value `app`. Then, go into the `repolist` directory and run the command `flask run`.

**IMPORTANT:**
Due to the request limiting of the GitHub API, which limits the amounts of request for non-authenticated users to 60 requests per hour, it is highly recommended, to authenticate using a GitHub personal authentication token, which can be generated here: https://github.com/settings/tokens.
Upon generating the token, declare the following environment variables, and set them to values given below:
 - `GITHUB_TOKEN=<valid github personal access token>`
 - `GITHUB_USER=<username of the account the token belongs to>`

### Running the tests
To run tests on the project and get info about the code coverage achieved, run `python3 -m pytest --cov=repolist.logic` in the root directory of the project

## API Endpoints
* /users/{username}/repos - List repos of a given user
* /users/{username}/stars - List the sum of star counts from all of the user's repos
* /users/{username}/languages - List the sum of stars from all of the user's repos

## Technologies
This project was created with:
* python version: 3.10.1
* flask version: 2.0.2
* aiohttp version: 3.8.1

## Notes

* Included repo ID in the list of user's repositories.

## Improvement Ideas

* Providing API users with the ability to provide their own GitHub Personal Access Tokens to the API through HTTPS. That would make it so that the GitHubAPI request quota isn't shared across all of the application's users.
* Implementing some sort of response caching would help with not going above the GitHubAPI request quota.
* Getting the list of all languages across all of the user's repos requires a large number of requests (one per repo). Agregating that data is some sort of way would greatly reduce the risk of request qouta being exceeded by only a few API calls.