import io
import time
import websocket
import picamera

# The URL of the WebSocket server
WEBSOCKET_URL = "wss://greenhouse-dashboard-testing-3c4c04ab9598.herokuapp.com/camera2"

def send_video_frames(url):
    ws = None
    try:
        # Establish a WebSocket connection
        ws = websocket.create_connection(url)
        with picamera.PiCamera() as camera:
            camera.resolution = (640, 480)  # Set a smaller resolution for faster streaming
            camera.framerate = 24  # Set frame rate
            camera.rotation = 270  # Rotate the camera
            time.sleep(2)  # Camera warm-up time

            stream = io.BytesIO()
            for _ in camera.capture_continuous(stream, 'jpeg',quality = 15 ,use_video_port=True):
                # Send the frame over the WebSocket connection
                stream.seek(0)
                ws.send(stream.read(), websocket.ABNF.OPCODE_BINARY)
                stream.seek(0)
                stream.truncate()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if ws:
            ws.close()

def run_forever(url):
    while True:
        try:
            send_video_frames(url)
            print("Reconnecting after unexpected exit...")
            time.sleep(1)  # Wait a bit before trying to reconnect
        except Exception as e:
            print(f"Error during streaming: {e}")
            time.sleep(1) # Wait before retrying

if __name__ == "__main__":
    run_forever(WEBSOCKET_URL)

