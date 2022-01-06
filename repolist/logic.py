import asyncio
import re

import aiohttp


class InvalidUserError(Exception):
    pass


class UserQuotaExceededError(Exception):
    pass


class API:

    def __init__(self, url, *, username=None, auth_token=None):
        """API Object Consstructor

        Args:
            url (str): GitHubAPI URL
            username (str, optional): Username of the user authenticating
                to the GitHubAPI. Defaults to None.
            auth_token (str, optional): GitHub Personal Access Token.
                Defaults to None.
        """
        self.api_url = url
        self._headers = {}
        if auth_token is not None:
            self._headers['Authorization'] = f'token {auth_token}'
        if username is not None:
            self._headers['User-Agent'] = username

    async def _yield_repos(self, repos):
        """Converts repositories returned by GitHubAPI into dictionaries
                containing their id, full_name and star_count

        Args:
            repos (list): List of repositories returned by GitHubAPI

        Yields:
            dict: Dictionary containing repository id, full_name and
                    stargazer_count of the following format:
                {
                    'id': ID of the repository,
                    'name': full name of the repository,
                    'star_count': stargazer_count of the repository
                }
        """
        for repo in repos:
            res = {
                'id': repo['id'],
                'name': repo['full_name'],
                'star_count': repo['stargazers_count']
            }
            yield res

    async def _fetch(self, session, url, *, headers={}, params={}):
        """Fetches given URL

        Args:
            session (aiohttp.ClientSession): session on wihch to call
                the .get() method
            url (str): URL to fetch
            headers (dict, optional): request headers. Defaults to {}.
            params (dict, optional): request query string parameters.
                Defaults to {}.

        Raises:
            InvalidUserError: If user of the username given in the
                URL does not exist
            UserQuotaExceededError: If GitHubAPI request quota has
                been exceeded

        Returns:
            aiohttp.ClientResponse: Response fetched from given URL
        """
        res = await session.get(url, headers=headers, params=params)
        if (status := res.status) == 404:
            raise InvalidUserError
        elif status == 403:
            raise UserQuotaExceededError
        return res

    async def get_user_repos(self, username):
        """Gets repositories of given user from the GitHubAPI

        Args:
            username (string): Username of the user

        Yields:
            dict: Dictionary of the format:
                {
                    'id': ID of the repository,
                    'name': name of the repository,
                    'star_count': star count of the repository
                }
        """
        async with aiohttp.ClientSession() as session:
            async def fetch_page(page):
                url = f'{self.api_url}/users/{username}/repos'
                kwargs = {
                    'headers': self._headers,
                    'params': {
                        'per_page': 100,
                        'page': page
                    }
                }
                return await self._fetch(session, url, **kwargs)

            res = await fetch_page(1)
            async with res:
                raw_repos = await res.json()
                async for repo in self._yield_repos(raw_repos):
                    yield repo

            # Stops function's execution if all of the user's
            # repos are on the first page.
            if (links := res.headers.get('Link')) is None:
                return

            # Searches for the number of the last page of
            # results in the 'Link' header of the first response
            last_page_match = re.search(
                r'page=(\d+)>; rel="last"', links)
            last_page = int(last_page_match.group(1))

            # Fetches all the other pages
            tasks = [fetch_page(i) for i in range(2, last_page + 1)]
            for task in asyncio.as_completed(tasks):
                res = await task
                async with res:
                    raw_repos = await res.json()
                    async for repo in self._yield_repos(raw_repos):
                        yield repo

    async def get_user_star_total(self, user):
        """Calculates the total amount of star_count across all of
            the given user's GitHub repositories

        Args:
            user (str): Username of the GitHub user

        Returns:
            int: The total star count across all of the
                users GitHub repositories
        """
        repos = self.get_user_repos(user)
        return sum([repo['star_count'] async for repo in repos])

    async def get_users_language_list(self, user):
        """Creates an ordered list of the most popular programming
            languages across all of the given user's GitHub
            repositories, ranked from most popular, to least popular
            by the number of bytes written in a given language.

        Args:
            user (str): Username of the user

        Returns:
            list: List of user's most popular programming languages.
                Each language is a dictionary of the format:
                {
                    'language': language name,
                    'byte_count': numer of bytes written
                        in a given language
                }
        """
        langs = {}
        async with aiohttp.ClientSession() as session:
            repos = self.get_user_repos(user)
            tasks = []
            async for repo in repos:
                url = f"{self.api_url}/repos/{repo['name']}/languages"
                coro = self._fetch(session, url, headers=self._headers)
                tasks.append(coro)

            for task in asyncio.as_completed(tasks):
                res = await task
                languages = await res.json()
                for language, bytes in languages.items():
                    if langs.get(language) is not None:
                        langs[language] += bytes
                    else:
                        langs[language] = bytes

        ranked_langs = sorted(
            langs.items(), key=lambda x: x[1], reverse=True)
        ret = []
        for key, value in ranked_langs:
            ret.append({'language': key, 'byte_count': value})
        return ret
