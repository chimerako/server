from flask import Flask, request, render_template, jsonify
from flask_cors import CORS, cross_origin
import subprocess
import psutil
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from dateutil.parser import parse
import json
import os
import time

# Set timezone, e.g., to 'US/Eastern'
os.environ['TZ'] = 'Asia/Manila'
time.tzset()

app = Flask(__name__)
CORS(app)
scheduler = BackgroundScheduler()
scheduler.start()

ffmpeg_pids = {}
stream_info = {}

@app.route('/')
@cross_origin()
def index():
    return render_template('index.html', stream_info=json.dumps(stream_info))

def start_ffmpeg_stream(stream_id, source_url, destination_url, command_type):
    if command_type == "command1":
        # Existing logic for Command 1
        ffmpeg_process = subprocess.Popen(['ffmpeg', '-re', '-i', source_url, '-acodec', 'copy', '-vcodec', 'copy', '-f', 'flv', destination_url])
    elif command_type == "command2":
        # Logic for Command 2 using yt-dlp
        yt_dlp_process = subprocess.Popen(['yt-dlp', '-f', 'b', '-g', source_url], stdout=subprocess.PIPE)
        yt_dlp_output, _ = yt_dlp_process.communicate()
        yt_dlp_url = yt_dlp_output.strip().decode('utf-8')
        ffmpeg_process = subprocess.Popen(['ffmpeg', '-re', '-i', yt_dlp_url, '-acodec', 'copy', '-vcodec', 'copy', '-f', 'flv', destination_url])
    elif command_type == "command3":
        # Logic for Command 3 using streamlink
        streamlink_process = subprocess.Popen(['streamlink', '-http-header', 'User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0', '--http-header', f'Referer={source_url}', source_url, 'best', '-O'], stdout=subprocess.PIPE)
        ffmpeg_process = subprocess.Popen(['ffmpeg', '-re', '-i', 'pipe:0', '-acodec', 'copy', '-vcodec', 'copy', '-f', 'flv', destination_url], stdin=streamlink_process.stdout)
    ffmpeg_pids[stream_id] = ffmpeg_process.pid

@app.route('/start/<stream_id>', methods=['POST'])
def start_stream(stream_id):
    data = request.get_json()
    command_type = data.get('command_type')
    source_url = data.get('source_url')
    destination_url = data.get('destination_url')

    # Check if all required data is present
    if not all([command_type, source_url, destination_url]):
        return jsonify({'error': 'Missing required data'}), 400

    # Start the ffmpeg stream with the specified parameters
    try:
        start_ffmpeg_stream(stream_id, source_url, destination_url, command_type)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Update stream info
    stream_info[stream_id] = {
        'source_url': source_url,
        'destination_url': destination_url,
        'command_type': command_type,
        'status': 'running'
    }

    return jsonify({'message': f"Stream {stream_id} started successfully"}), 200

@app.route('/stop/<stream_id>', methods=['GET'])
@cross_origin()
def stop_stream(stream_id):
    pid = ffmpeg_pids.get(stream_id)
    if pid:
        try:
            psutil.Process(pid).terminate()
            del ffmpeg_pids[stream_id]
            stream_info[stream_id]['status'] = 'stopped'
            return jsonify({'message': f"Stream {stream_id} stopped successfully"}), 200
        except psutil.NoSuchProcess:
            return jsonify({'error': f"No such process for stream {stream_id}"}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': f"No stream {stream_id} to stop"}), 400

@app.route('/schedule/<stream_id>', methods=['POST'])
def schedule_stream(stream_id):
    data = request.get_json()
    command_type = data.get('command_type')
    source_url = data.get('source_url')
    destination_url = data.get('destination_url')
    schedule_time = data.get('schedule_time')

    # Check if all required data is present
    if not all([command_type, source_url, destination_url, schedule_time]):
        return jsonify({'error': 'Missing required data'}), 400

    # Convert schedule_time to a datetime object
    try:
        schedule_datetime = parse(schedule_time)
    except ValueError:
        return jsonify({'error': 'Invalid schedule time format'}), 400

    # Schedule the stream using APScheduler
    try:
        scheduler.add_job(
            start_ffmpeg_stream,
            'date',
            run_date=schedule_datetime,
            args=[stream_id, source_url, destination_url, command_type],
            id=stream_id
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Update stream info
    stream_info[stream_id] = {
        'source_url': source_url,
        'destination_url': destination_url,
        'command_type': command_type,
        'status': 'scheduled',
        'schedule_time': schedule_time
    }

    return jsonify({'message': f"Stream {stream_id} scheduled for {schedule_time}"}), 200


@app.route('/cancel_schedule/<stream_id>', methods=['GET'])
def cancel_schedule(stream_id):
    # Check if the stream is in the scheduler
    job = scheduler.get_job(stream_id)
    if job:
        try:
            job.remove()  # Remove the scheduled job from APScheduler
            stream_info[stream_id]['status'] = 'schedule_canceled'
            return jsonify({'message': f"Scheduled stream {stream_id} canceled"}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': f"No scheduled stream {stream_id} to cancel"}), 400

@app.route('/stop_scheduled_stream/<stream_id>', methods=['GET'])
def stop_scheduled_stream(stream_id):
    # First, try to remove the job if it's scheduled
    job = scheduler.get_job(stream_id)
    if job:
        try:
            job.remove()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Next, stop the stream if it's already running
    pid = ffmpeg_pids.get(stream_id)
    if pid:
        try:
            psutil.Process(pid).terminate()
            del ffmpeg_pids[stream_id]
            stream_info[stream_id]['status'] = 'stopped'
            return jsonify({'message': f"Scheduled and running stream {stream_id} stopped successfully"}), 200
        except psutil.NoSuchProcess:
            return jsonify({'error': f"No such process for stream {stream_id}"}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    elif stream_id in stream_info:
        # If the stream was scheduled but not yet running
        stream_info[stream_id]['status'] = 'stopped'
        return jsonify({'message': f"Scheduled stream {stream_id} stopped successfully"}), 200
    else:
        return jsonify({'error': f"No scheduled or running stream {stream_id} to stop"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
