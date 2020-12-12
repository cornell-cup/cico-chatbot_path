from util import live_streaming
from util import nlp_util
from util import keywords
from util import make_response
from util import playtrack
from util import path_planning
from util import object_detection
from util import face_recognition
from util import utils
from util.api import weather
from util.api import restaurant
from topic_classifier import get_topic
from playsound import playsound
import re
import sys
import os
import corpus_and_adapter
import re

# for flask setup
import requests
import json
import io
import socket

print(os.getcwd())
credential_path = "api_keys/speech_to_text.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

url = "http://18.216.143.187/"

utils.set_classpath()


def main():
    print("Hello! I am C1C0. I can answer questions and execute commands.")
    while True:
        # gets a tuple of phrase and confidence
        answer = live_streaming.main()
        speech = live_streaming.get_string(answer)
        confidence = live_streaming.get_confidence(answer)
        print(speech)

        if "quit" in speech or "stop" in speech:
            break

        if("cico" in speech.lower() or "kiko" in speech.lower() or "c1c0" in speech.lower()) and \
                ("hey" in speech.lower()):
            # filter out cico since it messes with location detection
            speech = utils.filter_cico(speech)

            if face_recognition.isFaceRecognition(speech):
                print(face_recognition.faceRecog(speech))
                # task is to transfer over to facial recognition client program
            elif path_planning.isLocCommand(speech.lower()):
                print("Move command (itemMove, direction, moveAmmount): ")
                print(path_planning.pathPlanning(speech.lower()))
                # task is to transfer over to path planning on the system
            elif object_detection.isObjCommand(speech.lower()):
                print("Object to pick up: " +
                      object_detection.object_parse(speech.lower()))
                # task is to transfer over to object detection on the system
            else:
                # we don't want the text to be lowercase since it messes with location detection
                print(corpus_and_adapter.response_from_chatbot(speech))
                # send this element to AWS for response generation

                # begin the flask transfer now


if __name__ == '__main__':
    # playsound('sounds/cicoremix.mp3')
    main()
