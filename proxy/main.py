#!/usr/bin/python3
from flup.server.fcgi import WSGIServer
from webroot import app

if __name__ == "__main__":
	WSGIServer(app, bindAddress='/tmp/protection-proxy.sock').run()