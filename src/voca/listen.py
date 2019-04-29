# Silvius microphone client based on Tanel's client.py
__author__ = "dwk"

import argparse
from ws4py.client.threadedclient import WebSocketClient
import threading
import sys
import urllib.request, urllib.parse, urllib.error
import json

reconnect_mode = False
fatal_error = False


class MyClient(WebSocketClient):
    def __init__(
        self,
        url,
        mic=1,
        protocols=None,
        extensions=None,
        heartbeat_freq=None,
        byterate=16000,
        show_hypotheses=True,
        save_adaptation_state_filename=None,
        send_adaptation_state_filename=None,
        audio_gate=0,
    ):
        super(MyClient, self).__init__(url, protocols, extensions, heartbeat_freq)
        self.mic = mic
        self.show_hypotheses = show_hypotheses
        self.byterate = byterate
        self.save_adaptation_state_filename = save_adaptation_state_filename
        self.send_adaptation_state_filename = send_adaptation_state_filename
        self.chunk = 0
        self.audio_gate = audio_gate

    def send_data(self, data):
        self.send(data, binary=True)

    def opened(self):
        import pyaudio
        import audioop

        pa = pyaudio.PyAudio()
        sample_rate = self.byterate
        stream = None

        while stream is None:
            try:
                # try adjusting this if you want fewer network packets
                self.chunk = 2048 * 2 * sample_rate // self.byterate

                mic = self.mic
                if mic == -1:
                    mic = pa.get_default_input_device_info()["index"]
                    print("Selecting default mic", file=sys.stderr)
                print("Using mic #", mic, file=sys.stderr)
                stream = pa.open(
                    rate=sample_rate,
                    format=pyaudio.paInt16,
                    channels=1,
                    input=True,
                    input_device_index=mic,
                    frames_per_buffer=self.chunk,
                )
            except IOError as e:
                if e.errno == -9997 or e.errno == "Invalid sample rate":
                    new_sample_rate = int(
                        pa.get_device_info_by_index(mic)["defaultSampleRate"]
                    )
                    if sample_rate != new_sample_rate:
                        sample_rate = new_sample_rate
                        continue
                print("\n", e, file=sys.stderr)
                print(
                    "\nCould not open microphone. Please try a different device.",
                    file=sys.stderr,
                )
                global fatal_error
                fatal_error = True
                sys.exit(0)

        def mic_to_ws():  # uses stream
            try:
                print("\nLISTENING TO MICROPHONE", file=sys.stderr)
                last_state = None
                while True:
                    data = stream.read(self.chunk)
                    if self.audio_gate > 0:
                        rms = audioop.rms(data, 2)
                        if rms < self.audio_gate:
                            data = "\00" * len(data)
                    # if sample_chan == 2:
                    #    data = audioop.tomono(data, 2, 1, 1)
                    if sample_rate != self.byterate:
                        (data, last_state) = audioop.ratecv(
                            data, 2, 1, sample_rate, self.byterate, last_state
                        )

                    self.send_data(data)
            except IOError as e:
                # usually a broken pipe
                print(e)
            except AttributeError:
                # currently raised when the socket gets closed by main thread
                pass

            # to voluntarily close the connection, we would use
            # self.send_data("")
            # self.send("EOS")

            try:
                self.close()
            except IOError:
                pass

        threading.Thread(target=mic_to_ws).start()

    def received_message(self, m):

        response = json.loads(str(m))
        # print >> sys.stderr, "RESPONSE:", response
        # print >> sys.stderr, "JSON was:", m
        if response["status"] == 0:
            if "result" in response:
                trans = response["result"]["hypotheses"][0]["transcript"]
                if response["result"]["final"]:
                    if self.show_hypotheses:
                        print("\r%s" % trans.replace("\n", "\\n"), file=sys.stderr)
                    # print("%s" % trans.replace("\n", "\\n"), flush=True)  # final result!
                    print(m, flush=True)
                elif self.show_hypotheses:
                    print_trans = trans.replace("\n", "\\n")
                    if len(print_trans) > 80:
                        print_trans = "... %s" % print_trans[-76:]
                    print("\r%s" % print_trans, end=" ", file=sys.stderr)
            if "adaptation_state" in response:
                if self.save_adaptation_state_filename:
                    print(
                        "Saving adaptation state to %s"
                        % self.save_adaptation_state_filename,
                        file=sys.stderr,
                    )
                    with open(self.save_adaptation_state_filename, "w") as f:
                        f.write(json.dumps(response["adaptation_state"]))
        else:
            print(
                "Received error from server (status %d)" % response["status"],
                file=sys.stderr,
            )
            if "message" in response:
                print("Error message:", response["message"], file=sys.stderr)

            global reconnect_mode
            if reconnect_mode:
                import time

                print("Sleeping for five seconds before reconnecting", file=sys.stderr)
                time.sleep(5)

    def closed(self, code, reason=None):
        # print "Websocket closed() called"
        # print >> sys.stderr
        pass


def setup():
    content_type = "audio/x-raw, layout=(string)interleaved, rate=(int)16000, format=(string)S16LE, channels=(int)1"
    path = "client/ws/speech"

    parser = argparse.ArgumentParser(description="Microphone client for silvius")
    parser.add_argument(
        "-s",
        "--server",
        default="localhost",
        dest="server",
        help="Speech-recognition server",
    )
    parser.add_argument("-p", "--port", default="8019", dest="port", help="Server port")
    # parser.add_argument('-r', '--rate', default=16000, dest="rate", type=int, help="Rate in bytes/sec at which audio should be sent to the server.")
    parser.add_argument(
        "-d",
        "--device",
        default="-1",
        dest="device",
        type=int,
        help="Select a different microphone (give device ID)",
    )
    parser.add_argument(
        "-k",
        "--keep-going",
        action="store_true",
        help="Keep reconnecting to the server after periods of silence",
    )
    parser.add_argument("--save-adaptation-state", help="Save adaptation state to file")
    parser.add_argument(
        "--send-adaptation-state", help="Send adaptation state from file"
    )
    parser.add_argument(
        "--content-type",
        default=content_type,
        help="Use the specified content type (default is " + content_type + ")",
    )
    parser.add_argument(
        "--hypotheses",
        default=True,
        type=int,
        help="Show partial recognition hypotheses (default: 1)",
    )
    parser.add_argument(
        "-g",
        "--audio-gate",
        default=0,
        type=int,
        help="Audio-gate level to reduce detections when not talking",
    )
    args = parser.parse_args()

    content_type = args.content_type
    print("Content-Type:", content_type, file=sys.stderr)

    if args.keep_going:
        global reconnect_mode
        global fatal_error
        reconnect_mode = True
        while fatal_error == False:
            print("Reconnecting...", file=sys.stderr)
            run(args, content_type, path)
    else:
        run(args, content_type, path)


def run(args, content_type, path):
    uri = "ws://%s:%s/%s?%s" % (
        args.server,
        args.port,
        path,
        urllib.parse.urlencode([("content-type", content_type)]),
    )
    print("Connecting to", uri, file=sys.stderr)

    ws = MyClient(
        uri,
        byterate=16000,
        mic=args.device,
        show_hypotheses=args.hypotheses,
        save_adaptation_state_filename=args.save_adaptation_state,
        send_adaptation_state_filename=args.send_adaptation_state,
        audio_gate=args.audio_gate,
    )
    ws.connect()
    # result = ws.get_full_hyp()
    # print result.encode('utf-8')
    ws.run_forever()


def main():
    try:
        setup()
    except KeyboardInterrupt:
        print("\nexiting...", file=sys.stderr)


if __name__ == "__main__":
    main()
