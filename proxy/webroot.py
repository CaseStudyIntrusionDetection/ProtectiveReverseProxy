from flask import Flask

app = Flask("ProtectiveProxy")

@app.route('/')
def hello():
	return 'Hello, World! :D'


# development access
if __name__ == "__main__":
	app.run(host='0.0.0.0', port='8080', debug=True)