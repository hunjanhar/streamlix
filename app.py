from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import yt_dlp
from urllib.parse import urlparse, parse_qs
from collections import defaultdict
import threading
import os
import time
import ssl
import certifi
import requests
from bs4 import BeautifulSoup

ssl._create_default_https_context = ssl.create_default_context(cafile=certifi.where())

app = Flask(__name__)

progress_data = {}
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
    parsed = urlparse(url)
    video_id = parse_qs(parsed.query).get("v")
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id[0]}"
    return url

def format_size(bytes_size):
    if not bytes_size:
        return "Unknown"
    mb = bytes_size / (1024 * 1024)
    return f"{mb:.2f} MB"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = clean_url(request.form.get('url').strip())
        try:
            with yt_dlp.YoutubeDL({}) as ydl:
                ydl.extract_info(url, download=False)

            return redirect(url_for('download', video_url=url))

        except Exception as e:
            return render_template('index.html', message=str(e))

    return render_template('index.html')


@app.route('/download')
def download():
    video_url = request.args.get('video_url')
    try:
        with yt_dlp.YoutubeDL({}) as ydl:
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
        return redirect(url_for('download', video_url=video_url,message=True))

@app.route('/progress/<task_id>')
def progress(task_id):
    return jsonify({'progress': progress_data.get(task_id, 0)})

@app.route('/download_file/<format_id>')
def download_file(format_id):
    url = request.args.get('url')
    task_id = request.args.get('task_id')

    def run_download():

        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)

                if total:
                    percent = int(downloaded * 100 / total)
                    progress_data[task_id] = percent
                else:
                    progress_data[task_id] = min(progress_data.get(task_id, 0) + 5, 95)

            elif d['status'] == 'finished':
                progress_data[task_id] = 98

        try:
            os.makedirs("temp", exist_ok=True)

            ydl_opts = {
                'format': f"{format_id}+bestaudio/best",
                'merge_output_format': 'mp4',
                'outtmpl': 'temp/%(title).50s.%(ext)s',
                'progress_hooks': [progress_hook],
                'nocheckcertificate': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

            file_paths[task_id] = file_path
            progress_data[task_id] = 100

        except Exception as e:
            progress_data[task_id] = -1

    threading.Thread(target=run_download).start()
    return "started"

@app.route('/get_file/<task_id>')
def get_file(task_id):
    path = file_paths.get(task_id)

    for _ in range(10):
        if path and os.path.exists(path):
            response = send_file(path, as_attachment=True)

            def delete_file(p):
                time.sleep(10)
                if os.path.exists(p):
                    os.remove(p)

            threading.Thread(target=delete_file, args=(path,)).start()

            return response

        time.sleep(1)

    return "File not ready"

if __name__ == '__main__':
    app.run(debug=True)