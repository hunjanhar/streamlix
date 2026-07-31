from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import yt_dlp
from urllib.parse import urlparse, parse_qs
from collections import defaultdict
import threading
import os
import time
import tempfile
import ssl
import certifi
import requests
import uuid
from bs4 import BeautifulSoup

ssl._create_default_https_context = ssl.create_default_context(cafile=certifi.where())

app = Flask(__name__)
metrics = PrometheusMetrics(app)

TEMP_DIR = os.path.join(tempfile.gettempdir(), "streamlix_temp")
os.makedirs(TEMP_DIR, exist_ok=True)

progress_data = {}
error_messages = {}
file_paths = {}
from urllib.parse import urlparse

def youtube_thumbnail(url):
    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(url)

    if "youtube.com" in parsed.netloc:
        video_id = parse_qs(parsed.query).get("v")
        if video_id:
            return f"https://img.youtube.com/vi/{video_id[0]}/0.jpg"

    if "youtu.be" in parsed.netloc:
        video_id = parsed.path.strip("/")
        return f"https://img.youtube.com/vi/{video_id}/0.jpg"

    return None

def instagram_thumbnail(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")

        og_image = soup.find("meta", property="og:image")
        if og_image:
            return og_image["content"]
    except:
        return None
    
def get_thumbnail(url):
    if "youtube.com" in url or "youtu.be" in url:
        return youtube_thumbnail(url)

    if "instagram.com" in url:
        return instagram_thumbnail(url)

    return None

def clean_url(url):
    url = url.strip()
    parsed = urlparse(url)

    if "youtube.com" in parsed.netloc:
        video_id = parse_qs(parsed.query).get("v")
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id[0]}"
            
    if "youtu.be" in parsed.netloc:
        return url

    if "instagram.com" in parsed.netloc:
        path = parsed.path.rstrip('/')
        return f"https://www.instagram.com{path}/"

    return url

def get_base_ydl_opts():
    return {
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'instagram': {'check_connection': ['false']}},
    }

def format_size(bytes_size):
    if not bytes_size:
        return "Unknown"
    mb = bytes_size / (1024 * 1024)
    return f"{mb:.2f} MB"

@app.route('/', methods=['GET', 'POST'])
def index():
    message = request.args.get('message')

    if request.method == 'POST':
        url = clean_url(request.form.get('url', '').strip())
        try:
            with yt_dlp.YoutubeDL(get_base_ydl_opts()) as ydl:
                ydl.extract_info(url, download=False)
            return redirect(url_for('download', video_url=url))
        except Exception as e:
            return render_template('index.html', message="❌ Invalid or protected URL! Please verify your link configuration layout.")

    return render_template('index.html', message=message)


@app.route('/download')
def download():
    video_url = request.args.get('video_url')
    try:
        with yt_dlp.YoutubeDL(get_base_ydl_opts()) as ydl:
            info = ydl.extract_info(video_url, download=False)

            formats = info.get('formats', [])
            video_groups = defaultdict(list)
            audio_streams = []

            for f in formats:
                size = f.get('filesize') or f.get('filesize_approx')

                if f.get('vcodec') != 'none':
                    res = f.get('height')
                    if res:
                        video_groups[res].append({
                            'format_id': f['format_id'],
                            'ext': f.get('ext'),
                            'size': format_size(size),
                            'has_audio': f.get('acodec') != 'none'
                        })

                if f.get('vcodec') == 'none':
                    audio_streams.append({
                        'format_id': f['format_id'],
                        'ext': f.get('ext'),
                        'abr': f.get('abr'),
                        'size': format_size(size)
                    })

            video_groups = dict(sorted(video_groups.items()))
            thum = get_thumbnail(video_url)

            return render_template(
                'download.html',
                title=info.get('title'),
                video_groups=video_groups,
                audio_streams=audio_streams,
                video_url=video_url,
                thum=thum
            )
        
    except Exception as e:
        return render_template('index.html', message="Extraction failed. Video might be private or restricted.")

@app.route('/progress/<task_id>')
def progress(task_id):
    return jsonify({
        'progress': progress_data.get(task_id, 0),
        'error': error_messages.get(task_id)
    })

@app.route('/download_file/<format_id>')
def download_file(format_id):
    url = request.args.get('url')
    task_id = request.args.get('task_id')

    def run_download():
        progress_data[task_id] = 0
        error_messages[task_id] = None

        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                if total:
                    percent = int(downloaded * 100 / total)
                    progress_data[task_id] = min(percent, 99)
                else:
                    current = progress_data.get(task_id, 0)
                    progress_data[task_id] = min(current + 2, 95)
            elif d['status'] == 'finished':
                progress_data[task_id] = 99

        try:
            os.makedirs(TEMP_DIR, exist_ok=True)
            out_pattern = os.path.join(TEMP_DIR, f"{task_id}_%(title).50s.%(ext)s")

            if format_id and format_id not in ['best', 'undefined', 'None']:
                selected_format = f"{format_id}+bestaudio/best"
            else:
                selected_format = "bestvideo+bestaudio/best"

            ydl_opts = {
                'format': selected_format,
                'outtmpl': out_pattern,
                'merge_output_format': 'mp4',
                'progress_hooks': [progress_hook],
                'nocheckcertificate': True,
                'quiet': True,
                'no_warnings': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if 'requested_downloads' in info and info['requested_downloads']:
                    file_path = info['requested_downloads'][0]['filepath']
                else:
                    file_path = ydl.prepare_filename(info)

            # Fallback file path check in system TEMP_DIR
            if not os.path.exists(file_path):
                for f in os.listdir(TEMP_DIR):
                    if f.startswith(task_id):
                        file_path = os.path.join(TEMP_DIR, f)
                        break

            file_paths[task_id] = file_path
            progress_data[task_id] = 100

        except Exception as e:
            progress_data[task_id] = -1
            error_messages[task_id] = str(e)

    threading.Thread(target=run_download).start()
    return jsonify({"status": "started"})


@app.route('/get_file/<task_id>')
def get_file(task_id):
    for _ in range(60):
        path = file_paths.get(task_id)
        if path and os.path.exists(path):
            size_1 = os.path.getsize(path)
            time.sleep(0.5)
            size_2 = os.path.getsize(path)
            
            if size_1 == size_2 and size_1 > 0:
                response = send_file(path, as_attachment=True)

                def delete_file(p):
                    time.sleep(30)
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass
                
                threading.Thread(target=delete_file, args=(path,)).start()
                return response
        time.sleep(1)
    return redirect(url_for('index', message="File processing timed out on the server. Please try a different quality scale."))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)