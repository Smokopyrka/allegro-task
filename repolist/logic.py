from datetime import datetime
import aiohttp
import asyncio
import re
import os

class InvalidUserError(Exception):
    pass

class UserQuotaExceededError(Exception):
    pass

class API:

    def __init__(self):
        self.api_url = 'https://api.github.com'
        self._headers = {}
        if (token := os.environ.get('GITHUB_TOKEN')) != None:
            self._headers['Authorization'] = f'token {token}'
        if (user_agent := os.environ.get('GITHUB_USER')) != None:
            self._headers['User-Agent'] = user_agent

    async def _yield_repos(self, repos):
        for repo in repos:
            res = {
                'id': repo['id'],
                'name': repo['full_name'],
                'stars': repo['stargazers_count']
            }
            yield res
    
    async def _fetch(self, session, url, *, headers={}, params={}):
        res = await session.get(url, headers=headers, params=params)
        if (status := res.status) == 404:
            raise InvalidUserError
        elif status == 403:
            raise UserQuotaExceededError
        return res

    async def get_user_repos(self, username):
        url = f'{self.api_url}/users/{username}/repos'
        kwargs = {
            'headers': self._headers,
            'params': {
                'per_page': 100,
                'page': 1
            }
        }
        async with aiohttp.ClientSession() as session:
            res = await self._fetch(session, url, **kwargs)
            async with res:
                repos = await res.json()
                async for repo in self._yield_repos(repos):
                    yield repo

            if (links := res.headers.get('Link')) == None:
                return

            last_page_match = re.search(
                r'page=(\d+)>; rel="last"', links)
            last_page = int(last_page_match.group(1))

            tasks = []
            for num in range(2, last_page+1):
                kwargs = {
                    'headers': self._headers,
                    'params': {
                        'per_page': 100,
                        'page': num
                    }
                }
                coro = self._fetch(session, url, **kwargs)
                tasks.append(coro)
            
            for task in asyncio.as_completed(tasks):
                res = await task
                async with res:
                    repos = await res.json()
                    async for repo in self._yield_repos(repos):
                        yield repo

    async def get_user_star_total(self, user):
        repos = self.get_user_repos(user)
        return sum([repo['stars'] async for repo in repos])
    
    async def get_users_language_list(self, user):
        langs = {}
        async with aiohttp.ClientSession() as session:
            tasks = []
            repos = self.get_user_repos(user)
            async for repo in repos:
                repo_name = repo['name']
                url = f'{self.api_url}/repos/{repo_name}/languages'
                coro = self._fetch(session, url, headers=self._headers)
                tasks.append(coro)

            for task in asyncio.as_completed(tasks):
                res = await task
                languages = await res.json()
                for language, bytes in languages.items():
                    if langs.get(language) != None:
                        langs[language] += bytes
                    else:
                        langs[language] = bytes

        ranked_langs = sorted(langs.items(),
            key=lambda x: x[1], reverse=True)
        ret = []
        for key, value in ranked_langs:
            ret.append({'language': key, 'byte_count': value})
        return ret
