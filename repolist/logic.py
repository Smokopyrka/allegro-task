import asyncio
import re
from collections import defaultdict

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

    async def _fetch(self, session, url, *, headers={}, params={}):
        """Fetches given URL

        Args:
            session (aiohttp.ClientSession): Session used for making HTTP
            requests
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
        async for res in self._fetch_pages(username):
            async with res:
                raw_repos = await res.json()
                for repo in self._yield_repos(raw_repos):
                    yield repo
    
    async def _fetch_pages(self, username):
        """Fetches each page of user's repositories from the GitHubAPI. 
        Checks if all of user's repositories are on the first page of
        results, if not, grabs the number of the last page of results 
        from the first response's header and asynchronously fetches all
        the other pages.

        Args:
            username (str): Username of the GitHub user

        Yields:
            aiohttp.ClientResponse: Response containing user's repositories
                fetched from the GitHubAPI
        """
        async with aiohttp.ClientSession() as session:
            first_res = await self._fetch_repo_page(session, username, 1)
            yield first_res

            # Stops function's execution if all of the user's
            # repos are on the first page of the results.
            if (links := first_res.headers.get('Link')) is None:
                return

            # Searches for the number of the last page of
            # results in the 'Link' header of the first response
            last_page_match = re.search(
                r'page=(\d+)>; rel="last"', links)
            last_page = int(last_page_match.group(1))

            # Fetches all the other pages
            tasks = []
            for i in range(2, last_page + 1):
                task = asyncio.create_task(
                    self._fetch_repo_page(session, username, i))
                tasks.append(task)
            for res in asyncio.as_completed(tasks):
                yield await res

    async def _fetch_repo_page(self, session, username, page):
        """Fetches specified page of user's GitHub repositories from the
        GitHubAPI.

        Args:
            session (aiohttp.ClientSession): Session used for making HTTP
            requests
            username (str): Username of the GitHub user
            page (int): Number of the page to fetch

        Returns:
            aiohttp.ClientResponse: Response containing user's repositories
                fetched from the GitHubAPI
        """
        url = f'{self.api_url}/users/{username}/repos'
        kwargs = {
            'headers': self._headers,
            'params': {
                'per_page': 100,
                'page': page
            }
        }
        return await self._fetch(session, url, **kwargs)

    def _yield_repos(self, repos):
        """Converts repositories returned by GitHubAPI into dictionaries
        containing their id, full_name and star_count

        Args:
            repos (list): List of repositories returned by GitHubAPI

        Yields:
            dict: Dictionary containing repository id, full name and
                    star_count of the following format:
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
        langs = defaultdict(lambda: 0)
        async with aiohttp.ClientSession() as session:
            tasks = []
            async for repo in self.get_user_repos(user):
                url = f"{self.api_url}/repos/{repo['name']}/languages"
                coro = self._fetch(session, url, headers=self._headers)
                tasks.append(asyncio.create_task(coro))

            for task in asyncio.as_completed(tasks):
                res = await task
                repo_langs = await res.json()
                for lang_name, byte_count in repo_langs.items():
                    langs[lang_name] += byte_count

        ranked_langs = sorted(
            langs.items(), key=lambda x: x[1], reverse=True)
        ret = []
        for key, value in ranked_langs:
            ret.append({'language': key, 'byte_count': value})
        return ret
