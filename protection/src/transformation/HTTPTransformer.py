# coding: utf-8
from urllib.parse import unquote, urlsplit
from datetime import datetime
import re
import os
from copy import deepcopy
from string import punctuation

from ipaddress import ip_address

from src.transformation.DataTransformer import DataTransformer
import src.utils.list_utils as list_utils
from src.utils.list_utils import list_flatten
import src.utils.string_utils as string_utils


class HTTPTransformer(DataTransformer):

    @staticmethod
    def uri_transformation_wrapper(uri):
        """Wraps the transformation / cleansing steps for a URI string

        Args:
            uri (str): URI string

        Returns:
            dict: URI Object
        """
        # Split into netloc, path, query, fragment
        uri = HTTPTransformer.nested_uri_decode(uri)

        obj = HTTPTransformer.split_uri_into_components(uri)
        obj['netloc'] = obj['netloc']
        obj['path'] = HTTPTransformer.handle_path(obj['path'])
        obj['query'] = HTTPTransformer.handle_query(obj['query'])
        obj['fragment'] = obj['fragment']

        return obj

    @staticmethod
    def handle_path(path):
        """Transforms a URL path by:
        - Splitting at non-word characters (but keeping them)
        - Replacing Strings between those chars by `<PathString>`
        - Extensions (e.g., `css`, `js`) are kept

        Args:
            path (str): path to be transformed

        Returns:
            str: transformed path
        """
        reg = r'([^\w\s]+)'
        l = re.split(reg, path)

        # Handle extension (if existent)
        ext = os.path.splitext(path)[1]
        ext = "" if ext == "" else ext[1:]  # remove . at beginning

        l = [x for x in l if x != ""]

        l = ["<PathString>" if not re.match(reg, x) else x for x in l]

        if ext != "":
            l[-1] = ext

        # Split up parts consisting of multiple non-word chars (e.g., '/../' becomes ['/', '..', '/'])
        l = [string_utils.split_string_on_changing_char(x) if re.match(r"^[^\w\s]+$", x) else x for x in l]
        l = list_flatten(l)
        return " ".join(l)

    @staticmethod
    def handle_query(query_string):
        """Wrapper for query handling.

        Args:
            query_string (str): query string (possibly consisting of multiple queries, separated by '&')

        Returns:
            str: transformed query string
        """
        l = HTTPTransformer.query_to_splitted_list(query_string)
        transformed = HTTPTransformer.merge_query_list_to_string(l)
        return transformed

    @staticmethod
    def get_mask_string(s):

        # More input here 
        # https://www.sans.org/reading-room/whitepapers/logging/detecting-attacks-web-applications-log-files-2074
        # https://netman.aiops.org/~peidan/ANM2019/13.Security/ReadingLists/p80-Liang.pdf
        s = s.strip()

        regex_categories = {
            'singleChar': r'^[A-Za-z]{1}$',
            'onlyAlpha': r'^[A-Za-z]+$',
            'onlyNum': r'^(\d+(\.\d+)?)+$',
            'alphanum': r'^[A-Za-z0-9]+$',
            'mixed': r'^[A-Za-z0-9_]+$'
        }

        for token, regex in regex_categories.items():
            if re.match(regex, s):
                return f"[{token}]"
        
        return s
    
    @staticmethod
    def query_to_splitted_list(compl_query_str):
        """Splits a query string into a list per query. Then replaces query keys if existent and does the 
        split masking on the query values.

        Example:
        ```
        'platform=windows&category=office&id=42'
        ```
        is turned into
        ```
        [['<QueryKey>', '[onlyAlpha]'], ['<QueryKey>', '[onlyAlpha]'], ['<QueryKey>', '[onlyNum]']]
        ```

        Args:
            compl_query_str (str): query string (possibly consisting of multiple queries, separated by '&')

        Returns:
            nested list: nested list of shape [key_string, value_string] times n_queries
        """
        # Split on '&' into different queries and separate on '=' into key-value pairs
        q_list = [x.split("=", 1) if len(x.split("=")) == 2 else ["", x] for x in compl_query_str.split("&")]

        for i, elem in enumerate(q_list):
            # Replace query keys if existent
            if elem[0] != "":
                q_list[i][0] = "<QueryKey>"
            
            
            q_list[i][1] = HTTPTransformer.mask_single_query_param(elem[1])
        
        return q_list

    def mask_single_query_param(query_param):
        # Split on 1+ non-word chars
        reg = r'([^\w\s]+)'
        l = re.split(reg, query_param)
        # Kick out empty elements
        l = [x for x in l if x != ""]

        # Split non-word groups on changing chars
        l = [string_utils.split_string_on_changing_char(x) if re.match(r"^[^\w\s]+$", x) else x for x in l]
        l = list_flatten(l)

        l = [x.split(" ") if " " in x else x for x in l]
        l = list_flatten(l)

        # Replace with mask strings
        l = [HTTPTransformer.get_mask_string(x) for x in l]
        return " ".join(l)


    @staticmethod
    def merge_query_list_to_string(ql):
        """Merges a query list (created by `query_to_splitted_list`) into a string again.

        Example:
        ```
        [['<QueryKey>', '[onlyAlpha]'], ['<QueryKey>', '[onlyAlpha]'], ['<QueryKey>', '[onlyNum]']]
        ```
        is turned into
        ```
        '<QueryKey> = [onlyAlpha] ? <QueryKey> = [onlyAlpha] ? <QueryKey> = [onlyNum]'
        ```

        Args:
            ql (list): nested query list

        Returns:
            str: merged query list
        """
        l = []
        for single_query in ql:
            key = single_query[0]
            param_string = single_query[1]

            if key == "":
                l.append(param_string)
            else:
                l.append(f"{key} = {param_string}")

        l =  " ? ".join([x.strip() for x in l if x != ""])
        
        return l

        
    @staticmethod
    def split_uri_into_components(uri, CSIC=False):
        """Some preprocessing steps for a URI string:
        1. Transforming to lower-case
        2. Unquoting the HTTP encoding
        3. Splitting into netloc, path, query, ...

        Args:
            uri (str): URI String

        Returns:
            dict: URI Object
        """
        uri = uri.lower()
        if CSIC:
            # parse (it seems ISO-8859-1 encoding is used in the CSIC dataset - for the spanish characters such as ó or '%F3' as HTTP encoded)
            uri = unquote(uri, encoding="ISO-8859-1")
        else:
            uri = unquote(uri)

        # Split into URL components (Result keys: scheme, netloc, path, query, fragment)
        # SplitResult(scheme='http', netloc='localhost:8080', path='/tienda1/publico/vaciar.jsp', query='B2=Vaciar+carrito%27%3B+DROP+TABLE+[...]', fragment='')
        url_split = urlsplit(uri)

        return {
            "scheme": url_split.scheme,
            "netloc": url_split.netloc,
            "path": url_split.path,
            "query": url_split.query,
            "fragment": url_split.fragment
        }

    @staticmethod
    def nested_uri_decode(uri):
        """Repeatedly encodes a given uri until it doesn't change anymore (due to possible applied nested encoding).

        Args:
            uri (string): uri string

        Returns:
            uri: decoded uri string
        """
        while True:
            new_uri = unquote(uri)
            if new_uri == uri:
                break
            uri = new_uri
        return new_uri

    @staticmethod
    def handle_body(header_dict):
        out = []
        for key, val in header_dict.items():
            transformed = HTTPTransformer.mask_single_query_param(val)
            out.append("<HeaderKey> = "+transformed)
        
        return " ? ".join(out)

    @staticmethod
    def cleanse_tokenized_list(obj):
        """Cleanse the URI object's values w.r.t. non-alphanumeric characters.
        According elements are deleted.

        Args:
            obj (dict): URI object

        Returns:
            dict: Cleansed URI object
        """
        for key in obj:
            if type(obj[key]) is not str:
                obj[key] = HTTPTransformer.drop_non_alphanumeric_tokens_from_list(
                    obj[key])

        return obj

    @staticmethod
    def tokenize(string):
        """Splits a string at one of the following delimiters: / ? & = + :

        Args:
            string (str): string to be split
        """
        pat = "[\/?&=\+:]+"
        return re.split(pat, string)

    @staticmethod
    def dict_to_string(d):
        l = []
        for key in d:
            l.append(f"{key} {d[key]}")
        return " ".join(l)

    @staticmethod
    def drop_non_alphanumeric_tokens_from_list(str_list):
        """Drops completely non-alphanumeric tokens from a list.

        Args:
            str_list (list): String list

        Returns:
            list: String list
        """
        regex = re.compile('[a-zA-Z0-9]')
        return [x for x in str_list if regex.match(x)]

    @classmethod
    def request_to_text_wrapper(cls, request):
        text = []
        # 1. Handle REQUEST HEADER
        text.extend(HTTPTransformer.header_to_string_list(
            request['header'], 'request'))
        # 2. Handle RESPONSE HEADER
        text.extend(HTTPTransformer.header_to_string_list(
            request['honeypot']['response-header'], 'response'))
        # 3. Handle REQUEST TIMESTAMP
        text.append(datetime.fromtimestamp(request['timestamp']).fromtimestamp(
            request['timestamp']).strftime("request_day_%a request_hour_%H request_minute_%M"))
        # 4. Handle REQUEST METHOD + PROTOCOL
        text.append('request_method_' + request['request']['method'] +
                    ' request_protocol' + request['request']['protocol'])
        # 5. Handle RESPONSE INFO (hash, size, status-code)
        text.append(request['honeypot']['response-hash'] + " response_size_" + str(request['honeypot']['response-size'])
                    + " response_status_" + str(request['honeypot']['response-status-code']))

        # 6. Handle URL
        #  -> Split into netloc & query parts (split on "?")
        if '?' in request['request']['uri']:
            filepart = request['request']['uri'].split('?')[0]
            text.append(HTTPTransformer.url_params_to_string(
                request['request']['uri'].split('?')[1]))
        else:
            filepart = request['request']['uri']

        if filepart in ['/', '']:
            text.append('path_')
        for path in filepart.split('/'):
            if path != "":
                text.append('path_' + path)

        # Handle BODY
        if request['request']['method'] == "POST":
            text.append(HTTPTransformer.body_to_string(
                request['request']['body']))

        # 7. Handle IP
        ip_object = ip_address(request['sender']['ip'])
        text.append(("private_ip " if ip_object.is_private else "")
                    + ("global_ip " if ip_object.is_global else "")
                    + ("reserved_ip" if ip_object.is_reserved else ""))

        return ' '.join(text).lower()

    @staticmethod
    def header_to_string_list(header, type_prefix=""):
        """Converts a HTTP header into a list of words. Several value parameters are transformed:
        - Version numbers are deleted or replaced by the string 'version'
        - For dates, minutes and seconds are removed
        - And others (see code).

        Args:
                header (dict): HTTP header as dict (representing the key-value pairs)
                type_prefix (str, optional): prefix for header type (e.g. `request` or `response`). Defaults to "".

        Returns:
                list: A list of words generated from the header, each prefixed with `type_prefix` + `_header_`
        """
        t = []

        for key, value in header.items():
            key_low = key.lower()
            if key_low == 'cookie':
                t.append(HTTPTransformer.url_params_to_string(
                    value, prefix=type_prefix + '_cookie', delimiter=';'))
            else:
                t.append(type_prefix + '_header_' + key_low)

                if key_low in ['date', 'expires', 'last-modified', 'if-modified-since', 'if-unmodified-since']:
                    t.append(re.sub(r':\d\d:\d\d', '', value).replace(' ', ''))
                elif key_low in ['x-powered-by', 'server', 'user-agent']:
                    t.append(re.sub(r'(\d+(.|_))*\d+',
                                    'version', value).replace(' ', ''))
                elif key_low in ['accept', 'accept-language']:
                    t.append(re.sub(r';?q=[\d.]+', '', value).replace(' ', ''))
                else:
                    t.append(re.sub(r'[^a-zA-Z0-9]', '', value))
        return t

    @staticmethod
    def transform_header(header):
        h = {}
        for key, value in header.items():
            key_low = key.lower()
            if key_low == 'cookie':
                # TODO: Handle cookie according to LDA Preprocess?
                # HTTPTransformer.url_params_to_string(
                #    value, prefix=type_prefix + '_cookie', delimiter=';')
                h['cookie'] = HTTPTransformer.tokenize(value)
            else:
                if key_low in ['date', 'expires', 'last-modified', 'if-modified-since', 'if-unmodified-since']:
                    h[key_low] = re.sub(r':\d\d:\d\d', '',
                                        value).replace(' ', '')
                elif key_low in ['x-powered-by', 'server', 'user-agent']:
                    h[key_low] = re.sub(r'(\d+(.|_))*\d+',
                                        'version', value).replace(' ', '')
                elif key_low in ['accept', 'accept-language']:
                    h[key_low] = re.sub(r';?q=[\d.]+', '',
                                        value).replace(' ', '')
                else:
                    h[key_low] = re.sub(r'[^a-zA-Z0-9]', '', value)
        return h

    @classmethod
    def body_to_string(cls, body):
        """Converts the body of a HTTP post request into a string of words. The
        words represent the relevant classes of characters which appear in the value,
        e.g. value_alphanum for alphanumerical characters (for the complete list,
        see the dict called regToCategory above). 

        Example: `key=123` becomes `post_key value_alphanum value_onlyText value_short_string value_num value_onlyNum`.

        Args:
            body (dict): HTTP body key-value pairs.

        Returns:
            str: transformed body.
        """
        t = ""
        for name, value in body.items():
            if t != "":
                t += " "

            t += "post_" + name
            for category, regex in cls.regex_categories.items():
                t += "" if re.search(regex,
                                     value) == None else " value_" + category
        return t

    @classmethod
    def url_params_to_string(cls, params, prefix='get', delimiter='&'):
        """Converts url parameters into a string of words. The words represent the
        relevant classes of characters which appear in the values of the key-value
        pairs. This is analogous to the `bodyToText` function.

        Args:
                params (str): The url parameters to transform, e.g. "sort=description&page=2"
                prefix (str, optional): Prefix specifying the request type. Defaults to 'get'.
                delimiter (str, optional): The delimiter at which the parameters are split. Defaults to '&'.

        Returns:
                str: transformed url parameters.
        """
        t = ""
        for param in params.split(delimiter):
            if t != "":
                t += " "

            parts = param.split('=')
            if len(parts) > 1:
                name, value = parts[0], unquote(parts[1])

                t += prefix + "_" + name
                for category, regex in cls.regex_categories.items():
                    t += "" if re.search(regex,
                                         value) == None else " value_" + category
            else:
                t += prefix + "_" + param
        return t

    @staticmethod
    def transform_url_params(params):
        pass

    @staticmethod
    def cleanse_request(request):
        """Removes information from a request that should not be there - e.g., the attack label.

        Args:
            request (dict): request object to be cleansed

        Returns:
            dict: cleansed request object
        """
        # Make copy to maintain original dict.
        request = deepcopy(request)
        # Cleanse Header
        rmv_header_keys = ['X-ZAP-Scan-ID']
        for key in rmv_header_keys:
            request['header'].pop(key)

        return request

    @classmethod
    def replace_regex_categories(cls, input):
        t = ""
        for category, regex in cls.regex_categories.items():
            t += "" if re.search(regex,
                                 input) == None else " value_" + category
        return t
