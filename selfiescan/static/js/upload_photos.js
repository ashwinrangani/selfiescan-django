document.addEventListener('DOMContentLoaded', () => {

const uploadedPhotos = document.getElementById('upload_data');
const uploadForm = document.getElementById('upload_photos');
const selectedPhotos = document.getElementById('selected-photos');
const progressBarContainer = document.getElementById('progressBarContainer');
const progressBar = document.getElementById('progressBar');

let total_upload_count = parseInt(uploadForm.dataset.uploadCount) || 0;
const isUnlimited = uploadForm.dataset.unlimitedUpload === 'true';
const billingURL = uploadForm.dataset.billingUrl;

const MAX_PARALLEL = 3;

let uploadQueue = [];
let activeUploads = 0;
let initialTotal = 0;
let totalFiles = 0;
let uploadedFiles = 0;
let failedUploads = 0;

const notyf = new Notyf({ duration: 20000, dismissible: true });
window.addEventListener("offline", () => {
    notyf.error("Internet connection lost");
});
window.addEventListener("online", () => {
    notyf.success("Back online");
    if (isUploading) {
        startUploadQueue();
    }
});
/* ---------------- Subscription Dialog ---------------- */
function openSubDialog() {
    const backdrop = document.getElementById("sub-dialog-backdrop");
    backdrop.style.display = "flex";
}
 
function closeSubDialog() {
    const backdrop = document.getElementById("sub-dialog-backdrop");
    backdrop.style.display = "none";
}
 
// Wire close button and dismiss button
document.getElementById("sub-dialog-close").onclick   = closeSubDialog;
document.getElementById("sub-dialog-dismiss").onclick = closeSubDialog;
 
// Close on backdrop click
document.getElementById("sub-dialog-backdrop").addEventListener("click", function(e) {
    if (e.target === this) closeSubDialog();
});
 
document.getElementById("upgrade-plan-btn").onclick = function () {
    if (billingURL) window.location.href = billingURL;
    closeSubDialog();
};

function validate_input(files){
    const allowed = ['image/jpeg','image/png','image/psd','image/jpg','image/webp'];
    for (let f of files){
        if(!allowed.includes(f.type)){
            notyf.error("Invalid file type!");
            return false;
        }
    }
    return true;
}

// Prevent browser from opening dropped files
["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
    document.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
    });
});

/* ---------------- Drag & Drop ---------------- */
const dragArea = document.getElementById("drag-area");

dragArea.addEventListener("dragenter", () => dragArea.classList.add("drag-active"));
dragArea.addEventListener("dragleave", () => dragArea.classList.remove("drag-active"));
dragArea.addEventListener("dragover",  (e) => { e.preventDefault(); dragArea.classList.add("drag-active"); });

dragArea.addEventListener("drop", (e) => {
    e.preventDefault();
    dragArea.classList.remove("drag-active");
    const files = Array.from(e.dataTransfer.files);
    if (!files.length) return;
    if (!validate_input(files)) return;
    addFilesToQueue(files);
    uploadedPhotos.value = "";
});

/* ---------------- Upload Card ---------------- */
function createUploadCard(item){

    const queue = document.getElementById("upload-queue");

    // Show queue section
    const section = document.getElementById("queue-section");
    if (section) section.style.display = "block";

    // Card — vertical flex layout for grid
    const card = document.createElement("div");
    card.className = "upload-item";
    card.id = "upload-" + item.id;

    // Top row: icon + size
    const top = document.createElement("div");
    top.className = "item-top";

    const icon = document.createElement("div");
    icon.className = "item-icon";
    icon.innerHTML = `<span class="icon-[tabler--photo] size-3.5"></span>`;

    const size = document.createElement("span");
    size.className = "item-size font-semibold text-primary";
    size.textContent = (item.file.size / (1024 * 1024)).toFixed(1) + " MB";

    top.appendChild(icon);
    top.appendChild(size);

    // Filename
    const name = document.createElement("span");
    name.className = "item-name";
    name.textContent = item.file.name;

    // Status
    const status = document.createElement("span");
    status.className = "item-status";
    status.textContent = "Waiting...";

    // Progress bar
    const track = document.createElement("div");
    track.className = "item-bar-track";
    const progressBar = document.createElement("div");
    progressBar.className = "item-bar-fill";
    track.appendChild(progressBar);

    // Retry button
    const retryBtn = document.createElement("button");
    retryBtn.className = "btn btn-xs btn-error btn-retry hidden";
    retryBtn.textContent = "Retry";

    retryBtn.onclick = function(){
        if (failedUploads > 0) failedUploads--;
        retryBtn.classList.add("hidden");
        card.classList.remove("item-failed");
        icon.className = "item-icon";
        icon.innerHTML = `<span class="icon-[tabler--photo] size-3.5"></span>`;
        status.textContent = "Retrying...";
        item.retries = 0;
        uploadQueue.push(item);
        startUploadQueue();
    };

    card.appendChild(top);
    card.appendChild(name);
    card.appendChild(status);
    card.appendChild(track);
    card.appendChild(retryBtn);
    queue.appendChild(card);

    // Update count badge
    const countBadge = document.getElementById("queue-count");
    if (countBadge) {
        const total = queue.querySelectorAll(".upload-item").length;
        countBadge.textContent = total + (total === 1 ? " file" : " files");
    }

    item.ui = { card, icon, status, progressBar, retryBtn };
}

/* ---------------- File Select ---------------- */
uploadedPhotos.addEventListener('change', (e) => {
    const files = e.target.files;
    if(!validate_input(files)) return;
    addFilesToQueue(files);
     uploadedPhotos.value = "";
});

function addFilesToQueue(files){
    for(let file of files){
        const item = {
            id: crypto.randomUUID(),
            file: file,
            status: "pending",
            retries: 0
        };
        uploadQueue.push(item);
        createUploadCard(item);
    }
    initialTotal += files.length;
    totalFiles = initialTotal;
    selectedPhotos.textContent = "Photos Selected: " + totalFiles;
}

/* ---------------- Submit ---------------- */
let isUploading = false;

uploadForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    if (isUploading) {
    notyf.error("Upload already in progress");
    return;
}

    if(uploadQueue.length === 0 && activeUploads === 0){
    notyf.error("Please select photos");
    return;
}

    const totalCount = total_upload_count + uploadQueue.length;
    if (!isUnlimited && totalCount > 100) {
        
        openSubDialog();
        return;
    }

    isUploading = true;
    document.getElementById("submitBtn").disabled = true;
    progressBarContainer.classList.remove("hidden");
    startUploadQueue();
});

/* ---------------- Queue Manager ---------------- */
function startUploadQueue(){
    while(activeUploads < MAX_PARALLEL && uploadQueue.length){
        const item = uploadQueue.shift();
        activeUploads++;
        uploadSingleFile(item);
    }
}

/* ---------------- Single Upload ---------------- */
async function uploadSingleFile(item){

    item.ui.card.classList.add("item-uploading");
    item.ui.icon.innerHTML = `<span class="icon-[tabler--loader-2] size-3.5 spin"></span>`;

    const csrfToken = uploadForm.querySelector('[name=csrfmiddlewaretoken]').value;

    const sessionSelect = document.getElementById("session-select");
    const sessionId = sessionSelect && sessionSelect.value ? sessionSelect.value : null;

    try {
        // ✅ STEP 1: Get presigned URL
        const presignedRes = await fetch(
            `${uploadForm.dataset.presignedUrl}?file_name=${encodeURIComponent(item.file.name)}&file_type=${item.file.type}`
        );

        if (!presignedRes.ok) throw new Error("Failed to get upload URL");

        const presignedData = await presignedRes.json();

        // ✅ STEP 2: Upload to S3 with progress
        await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.upload.onprogress = function(e){
                if(e.lengthComputable){
                    const percent = Math.round((e.loaded / e.total) * 100);
                    item.ui.progressBar.style.width = percent + "%";
                    item.ui.status.textContent = percent + "%";
                }
            };

            xhr.onload = function(){
                if (xhr.status === 200) {
                    resolve();
                } else {
                    reject("S3 upload failed");
                }
            };

            xhr.onerror = function(){
                reject("S3 upload error");
            };

            xhr.open("PUT", presignedData.url, true);
            xhr.setRequestHeader("Content-Type", item.file.type);
            xhr.send(item.file);
        });

        // ✅ STEP 3: Notify Django (VERY IMPORTANT)
        const completeRes = await fetch(uploadForm.dataset.uploadCompleteUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                file_key: presignedData.file_key,
                session_id: sessionId
            })
        });

        if (!completeRes.ok) throw new Error("Backend save failed");

        // ✅ SUCCESS
        uploadedFiles++;
        activeUploads--;

        item.ui.card.classList.remove("item-uploading");
        item.ui.status.textContent = "Done";
        item.ui.progressBar.style.width = "100%";
        item.ui.card.classList.add("item-success");
        item.ui.icon.className = "item-icon";
        item.ui.icon.innerHTML = `<span class="icon-[tabler--circle-check] size-3.5"></span>`;

        total_upload_count += 1;
        uploadForm.dataset.uploadCount = total_upload_count;

    } catch (error) {
        console.error(error);

        activeUploads--;
        item.ui.card.classList.remove("item-uploading");
        retryUpload(item);
    }

    // ✅ Update global progress
    const percent = Math.round((uploadedFiles / totalFiles) * 100);
    const remaining = totalFiles - uploadedFiles;

    progressBar.style.width = percent + "%";
    progressBar.textContent = percent + "%";

    selectedPhotos.textContent =
        `Uploaded ${uploadedFiles} / ${totalFiles} • Remaining ${remaining}`;

    if(uploadedFiles + failedUploads === initialTotal){
        isUploading = false;
        document.getElementById("submitBtn").disabled = false;

        if(failedUploads === 0){
            notyf.success("All photos uploaded. Processing started.");
        } else {
            notyf.error(`${failedUploads} uploads failed.`);
        }
    }

    startUploadQueue();
}

/* ---------------- Retry ---------------- */
function retryUpload(item){
    if(item.retries < 2){
        item.retries++;
        item.ui.status.textContent = "Retry " + item.retries + "/2";
        uploadQueue.push(item);
    } else {
        failedUploads++;
        item.ui.status.textContent = "Failed";
        item.ui.retryBtn.classList.remove("hidden");
        item.ui.card.classList.add("item-failed");
        item.ui.icon.className = "item-icon";
        item.ui.icon.innerHTML = `<span class="icon-[tabler--circle-x] size-3.5"></span>`;
    }
}

/* ---------------- Error Handler ---------------- */
function handleUploadError(response, statusCode, item){
    if(statusCode === 403 && response.redirect){
    openSubDialog();
        document.getElementById("upgrade-plan-btn").onclick = function () {
            window.location.href = response.redirect;

};
 
} else {
        retryUpload(item);
    }
}

});
