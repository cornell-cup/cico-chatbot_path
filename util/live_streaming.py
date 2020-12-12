from __future__ import division

import re
import sys
import os

from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums
from google.cloud.speech_v1p1beta1 import types
import pyaudio
from six.moves import queue

"""sets the credential path for Speech to Text api key """
credential_path = "../api_keys/speech_to_text.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

# Audio recording parameters
RATE = 24000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream(object):
    """ **Code from Google cloud speech to text documentation**
    Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)


def listen_print_loop(responses):
    """ ***Code from Google Speech to text documentation ***
    Iterates through server responses and prints them.
    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """

    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = ' ' * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            print(transcript + overwrite_chars)

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r'\b(exit|quit)\b', transcript, re.I):
                print('Exiting..')
                break

            num_chars_printed = 0


def returnResponseString(responses):
    """
    Returns a tuple of the most likely response and its confidence

    Parameters: response is an array
    """
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue
        transcript = result.alternatives[0].transcript
        confidence = result.alternatives[0].confidence
        overwrite_chars = ' ' * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            return(transcript + overwrite_chars, confidence)

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            # if re.search(r'\b(exit|quit)\b', transcript, re.I):
            #     print('Exiting..')
            #     break

            #num_chars_printed = 0


def get_string(t):
    """
    Returns the output string (1st element of the tuple)

    Parameter: t is a tuple
    Precondition: the first element is a string, second is a float
    """
    return t[0]


def get_confidence(t):
    """
    Returns the confidence (2nd element of the tuple)

    Parameter: t is a tuple
    Precondition: the first element is a string, second is a float
    """
    return t[1]


def append_to_file(filePath, message):
    """
    Adds a message [message] to the file specified in the file path [filePath]
    Used to keep track of the history of what has been said and the confidence
    """
    f = open(filePath, "a")
    f.write(message+"\n")

# def delete_file():
#     """
#     Clears the log.txt file
#     """
#     os.remove("log.txt")


def sub_main(profanityFilterBool):
    """
    *** Code taken from Google Cloud Speech to text documentation ***
    Turns on the profanity filter so bad words are censored and not printed
    """
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = 'en-US'  # a BCP-47 language tag
    sp_c_cico = {
        "phrases": ["cico", "Hey cico"],
        "boost": 20.0
    }  # speech_contexts_cico
    sp_c_kiko = {
        "phrases": ["Hey Kiko", "kiko", "Kiko", "kygo", "Kitty, girl"],
        "boost": 0
    }
    speech_contexts = [sp_c_cico, sp_c_kiko]
    client = speech_v1p1beta1.SpeechClient()
    # print(help(types.RecognitionConfig))
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
        enable_automatic_punctuation=True,
        speech_contexts=speech_contexts)

    streaming_config = types.StreamingRecognitionConfig(
        config=config,
        interim_results=True)

    with MicrophoneStream(RATE, CHUNK) as stream:

        audio_generator = stream.generator()
        requests = (types.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)

        responses = client.streaming_recognize(streaming_config, requests)
        # Now, put the transcription responses to use.
        solution = returnResponseString(responses)  # solution is the result

        append_to_file("log.txt", str(solution))

    return solution


def filter(t, switches):
    """
    Takes a string and filters out and replaces certain words

    This includes kiko to c1c0.

    Parameter t: Tuple containing string to edit and confidence level
    Precondition: t is a tuple - (s,f) s is a string and f is int or float
    """
    assert type(t) == tuple
    assert type(t[0]) == str and type(t[1]) in [float, int]
    s = get_string(t)
    result_string = s  # the variable to retur
    result_conf = get_confidence(t)
    for k in switches:
        num_occ = s.count(k)  # number of occurences
        for i in range(num_occ):
            #pos = result.find(k)
            pos = s.find(k)
            if pos != -1:  # if key found
                value = switches[k]
                result_string = result_string[:pos] + value\
                    + result_string[pos+len(value):]

    return (result_string, result_conf)


def main():
    """
    Returns a tuple of the spoken phrase as a string and the confidence

    Runs the full speech to text program with the profanity filter and specific
    words boosted
    """
    response = sub_main(True)
    switches = {'kiko': 'c1c0'}  # the words to replace

    result = filter(response, switches)
    return result


if __name__ == '__main__':
    main()
