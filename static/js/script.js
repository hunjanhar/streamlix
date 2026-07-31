function startDownload(format_id, video_url) {
    const safeFormatId = (format_id && format_id !== 'undefined') ? format_id : 'best';

    const allSelects = document.querySelectorAll('.form-control-sm');
    allSelects.forEach(selectElement => {
        if (selectElement.value !== format_id) {
            selectElement.selectedIndex = 0;
        }
    });

    const task_id = Date.now() + "_" + Math.floor(Math.random() * 1000);
    const progressContainer = document.getElementById("progressContainer");
    const alertoption = document.getElementById("error-download");
    const progressBar = document.getElementById("progressBar");
    const progressText = document.getElementById("progressText");

    progressContainer.style.display = "block";
    progressBar.value = 0;
    progressText.innerText = "0%";
    alertoption.innerHTML = "";

    fetch(`/download_file/${safeFormatId}?url=${encodeURIComponent(video_url)}&task_id=${task_id}`)
        .then(res => res.json())
        .then(data => {
            let lastProgress = 0;

            let interval = setInterval(() => {
                fetch(`/progress/${task_id}`)
                    .then(res => res.json())
                    .then(state => {
                        let p = state.progress;

                        if (p === -1 || state.error) {
                            clearInterval(interval);
                            progressContainer.style.display = "none";
                            alertoption.innerHTML = `
                                <div class="alert alert-danger mt-2" role="alert">
                                    <b>Download Failed!</b><br>${state.error || 'Server processing error.'}
                                </div>`;
                            return;
                        }

                        if (p >= lastProgress) {
                            lastProgress = p;
                            progressBar.value = p;

                            if (p === 99) {
                                progressText.innerText = "Processing media...";
                            } else {
                                progressText.innerText = p + "%";
                            }
                        }

                        if (p === 100) {
                            clearInterval(interval);
                            progressBar.value = 100;
                            progressText.innerText = "Starting Download...";

                            window.location.href = `/get_file/${task_id}`;

                            setTimeout(() => {
                                progressContainer.style.display = "none";
                            }, 4000);
                        }
                    })
                    .catch(err => {
                        clearInterval(interval);
                        progressContainer.style.display = "none";
                    });
            }, 1000);
        })
        .catch(err => {
            progressContainer.style.display = "none";
            alertoption.innerHTML = `
                <div class="alert alert-danger mt-2" role="alert">
                    <b>Network Error!</b> Could not reach server.
                </div>`;
        });
}

$(document).ready(function () {
    $('#downloadForm').on('submit', function () {
        var $btn = $('#submitBtn');
        var $spinner = $('#btnSpinner');
        var $text = $('#btnText');
        
        $text.text('Processing...');
        $spinner.removeClass('d-none');
        
        setTimeout(function() {
            $btn.prop('disabled', true);
        }, 0);
    });
});
