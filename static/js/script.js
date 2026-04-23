function startDownload(format_id, video_url) {
    const task_id = Date.now();

    const progressContainer = document.getElementById("progressContainer");
    const alertoption = document.getElementById("error-download");

    progressContainer.style.display = "block";
    alertoption.innerHTML = ""; // clear old errors

    fetch(`/download_file/${format_id}?url=${video_url}&task_id=${task_id}`);

    let interval = setInterval(() => {
        fetch(`/progress/${task_id}`)
            .then(res => res.json())
            .then(data => {
                let p = data.progress;

                document.getElementById("progressBar").value = p;
                document.getElementById("progressText").innerText = p + "%";

                // ✅ SUCCESS
                if (p === 100) {
                    clearInterval(interval);

                    setTimeout(() => {
                        window.location.href = `/get_file/${task_id}`;
                    }, 1000);
                }

                // ❌ ERROR
                if (p === -1) {
                    clearInterval(interval);

                    // hide progress bar
                    progressContainer.style.display = "none";

                    // show alert
                    alertoption.innerHTML = `
                        <div class="alert alert-warning alert-dismissible fade show mt-2" role="alert">
                            <strong>Download Failed!</strong> Please try again later.
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    `;
                }
            });
    }, 1000);
}
