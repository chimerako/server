from flask import Flask, request, render_template, jsonify
from flask_cors import CORS, cross_origin
import subprocess
import psutil

app = Flask(__name__)
CORS(app)

# Dictionary to store process IDs
ffmpeg_pids = {}

@app.route('/')
@cross_origin() # This will enable CORS for this route.
def index():
    return render_template('index.html')

@app.route('/start/<stream_id>', methods=['POST'])
def start_stream(stream_id):
    data = request.get_json()
    source_url = data.get('source_url')
    destination_url = data.get('destination_url')

    # Start the ffmpeg process
    ffmpeg_process = subprocess.Popen(['ffmpeg', '-re', '-i', source_url, '-acodec', 'copy', '-vcodec', 'copy', '-f', 'flv', destination_url])
    ffmpeg_pids[stream_id] = ffmpeg_process.pid

    return f"Stream {stream_id} started successfully", 200

@app.route('/stop/<stream_id>', methods=['GET'])
@cross_origin()
def stop_stream(stream_id):
    pid = ffmpeg_pids.get(stream_id)
    if pid:
        try:
            psutil.Process(pid).terminate()
            del ffmpeg_pids[stream_id]
            return f"Stream {stream_id} stopped successfully", 200
        except psutil.NoSuchProcess:
            return "No such process", 400
    else:
        return f"No stream {stream_id} to stop", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
