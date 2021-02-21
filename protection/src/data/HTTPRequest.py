

class HTTPRequest(object):

    def __init__(self, method, uri, protocol, headers, body):
        self.method = method
        self.uri = uri
        self.protocol = protocol
        self.headers = headers
        self.body = body

    def __str__(self):
        return f">> HTTP Request: \n" \
            f"   method: {self.method}\n" \
            f"   uri: {self.uri}\n" \
            f"   protocol: {self.protocol}\n" \
            f"   headers: {self.headers}\n" \
            f"   body: {self.body}"