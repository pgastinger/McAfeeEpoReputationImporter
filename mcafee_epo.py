# -*- coding: utf-8 -*-
"""
based on https://pypi.python.org/pypi/mcafee-epo/
"""
__author__ = "Peter Gastinger"
__copyright__ = "Copyright 2016, Raiffeisen Informatik GmbH"
__credits__ = [""]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Peter Gastinger"
__email__ = "peter.gastinger@r-it.at"
__status__ = "Development"
import json
import requests

requests.packages.urllib3.disable_warnings()

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

TIMEOUT = 2


class APIError(Exception):
    """Represents an error with the data received within a valid HTTP response."""


class Client:
    """Communicate with an ePO server.
    Instances are callable, pass a command name and parameters to make API calls.
    """

    def __init__(self, url, username, password, session=None, verify=True, timeout=5):
        """Create a client for the given ePO server.

        :param url: location of ePO server
        :param username: username to authenticate
        :param password: password to authenticate
        :param session: custom instance of :class:`requests.Session`, optional
        :param verify: if False, ignore SSL cert error messages
        :param timeout: Timeout for requests
        """

        self.url = url
        self.username = username
        self.password = password
        self.verify = verify
        self.timeout = timeout

        if session is None:
            session = requests.Session()

        self._session = session
        self._token = None

    def _get_token(self, _skip=False):
        """Get the security token if it's not already cached.

        :param bool _skip: used internally when making the initial request to get the token
        """

        if self._token is None and not _skip:
            self._token = self._request('core.getSecurityToken')

        return self._token

    def _request(self, name, **kwargs):
        """Format the request and interpret the response.
        Usually you want to use :meth:`__call__` instead.

        :param name: command name to call
        :param kwargs: arguments passed to :meth:`requests.request`
        :return: deserialized JSON data
        """

        kwargs.setdefault('auth', (self.username, self.password))
        params = kwargs.setdefault('params', {})
        # check whether the response will be json (default)
        is_json = params.setdefault(':output', 'json') == 'json'
        # add the security token, unless this is the request to get the token
        params.setdefault('orion.user.security.token', self._get_token(_skip=name == 'core.getSecurityToken'))
        url = urljoin(self.url, 'remote/{}'.format(name))

        if kwargs.get('data') or kwargs.get('json') or kwargs.get('files'):
            # use post method if there is post data
            request_result = self._session.post(url, **kwargs, verify=self.verify, timeout=self.timeout)
        else:
            request_result = self._session.get(url, **kwargs, verify=self.verify, timeout=self.timeout)

        # check that there was a valid http response
        request_result.raise_for_status()
        text = request_result.text

        if not text.startswith('OK:'):
            # response body contains an error
            raise APIError(text)

        return json.loads(text[3:]) if is_json else text[3:]

    def __call__(self, name, *args, **kwargs):
        """Make an API call by calling this instance.
        Collects arguments and calls :meth:`_request`.

        ePO commands take positional and named arguments.  Positional arguments are internally numbered "param#" and
        passed as named arguments.

        Files can be passed to some commands.  Pass a dictionary of ``'filename': file-like objects``, or other formats
        accepted by :meth:`requests.request`.  This command will not open files, as it is better to manage that in a
        ``with`` block in calling code.

        :param str name: command name to call
        :param args: positional arguments to command
        :param kwargs: named arguments to command
        :param dict params: named arguments that are not valid Python names can be provided here
        :param dict files: files to upload to command
        :return: deserialized JSON data
        """

        params = kwargs.pop('params', {})
        files = kwargs.pop('files', {})

        for i, item in enumerate(args, start=1):
            params['param{}'.format(i)] = item

        params.update(kwargs)
        return self._request(name, params=params, files=files)
