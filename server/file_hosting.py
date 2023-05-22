from flask import Flask, render_template
from datetime import datetime
from flask import render_template, Flask

app = Flask(__name__)

@app.route('/<file_name>')
def get_log(file_name):
    with open(f'C:/Users/joe/Documents/Inventory-Manager/server/data/{file_name}.json') as file:
        lines = file.readlines()
        lines = [line.rstrip() for line in lines]
        lines = lines[::-1]
    return render_template("index.html", list_to_send=lines)

if __name__ == "__main__":
    app.run(host='10.0.0.93', port='80', debug=False, threaded=True)