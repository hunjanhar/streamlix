function startDownload(format_id, video_url) {
    const task_id = Date.now();

    const progressContainer = document.getElementById("progressContainer");
    const alertoption = document.getElementById("error-download");

    progressContainer.style.display = "block";
    alertoption.innerHTML = "";

    fetch(`/download_file/${format_id}?url=${video_url}&task_id=${task_id}`);

    let interval = setInterval(() => {
        fetch(`/progress/${task_id}`)
            .then(res => res.json())
            .then(data => {
                let p = data.progress;


                document.getElementById("progressBar").value = p;
                document.getElementById("progressText").innerText = p + "%";

                if (p === 100) {
                    clearInterval(interval);

                    setTimeout(() => {
                        window.location.href = `/get_file/${task_id}`;
                    }, 1000);
                }
                if (p === -1) {
                    clearInterval(interval);
                    progressContainer.style.display = "none";

                    let errorMsg = data.error || "Download failed! Please try again later.";

                    alertoption.innerHTML = `
                        <div class="alert alert-warning alert-dismissible fade show mt-2" role="alert">
                            <strong>Download Failed!</strong> ${errorMsg}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    `;
                }
            });
    }, 1000);
}
