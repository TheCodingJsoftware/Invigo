"""
This script is seperate from the entire client-end project
and is not intended for the client to use this script.
"""

import calendar
import json
import os
import sched
import threading
import time
from os import listdir
from os.path import isfile, join

import requests
from flask import Flask, current_app, render_template, send_file, url_for

app = Flask(__name__)


@app.route("/")
def index() -> None:
    """
    It renders the index.html template with the variables downloadableRecordings, searchValue,
    colonySearchList, monthsList, daysList, and recordingStatus

    Returns:
      The webpage
    """
    # fileNames: list[str] = []
    # downloadLinks: list[str] = []
    # data = loadJson()
    # for fileName in data:
    #     newFileName: str = fileName.replace("_", ":").replace(".mp3", "")
    #     fileNames.append(newFileName)
    #     downloadLinks.append(getDownloadLink(fileName=fileName))
    # fileNames.reverse()
    # downloadLinks.reverse()
    # downloadableRecordings = zip(fileNames, downloadLinks)
    return render_template(
        "index.html",
        # downloadableRecordings=downloadableRecordings,
        # searchValue="",
        # colonySearchList=getColonyList(),
        # monthsList=getMonthsList(),
        # daysList=getDaysList(),
        # recordingStatus=getRecordingStatus(),
    )


# @app.route("/<file_name>")
# def search(file_name):
#     """Main page

#     Returns:
#         _type_: webpage
#     """
#     fileNames: list[str] = []
#     downloadLinks: list[str] = []

#     for fileName in data:
#         if file_name.lower() in fileName.lower():
#             newFileName: str = fileName.replace("_", ":").replace(".mp3", "")
#             fileNames.append(newFileName)
#             downloadLinks.append(getDownloadLink(fileName=fileName))
#     fileNames.reverse()
#     downloadLinks.reverse()
#     downloadableRecordings = zip(fileNames, downloadLinks)
#     return render_template(
#         "index.html",
#         downloadableRecordings=downloadableRecordings,
#         searchValue=file_name,
#         colonySearchList=getColonyList(),
#         monthsList=getMonthsList(),
#         daysList=getDaysList(),
#         recordingStatus=getRecordingStatus(),
#     )


# def downloadThread() -> None:
#     """update database every 5 minutes"""
#     while True:
#         downloadDatabase()
#         time.sleep(300)
# threading.Thread(target=downloadThread).start()
app.run(host="10.0.0.217", port=5000, debug=False, threaded=True)
