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
let totalFiles = 0;
let uploadedFiles = 0;

const notyf = new Notyf({ duration: 20000 ,dismissible: true });

document.getElementById("upgrade-plan-btn").onclick = function () {
    if (billingURL) window.location.href = billingURL;
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

/* ---------------- Drag & Drop ---------------- */

uploadForm.addEventListener("dragover",(e)=>{
    e.preventDefault();
    uploadForm.classList.add("border-primary");
});

uploadForm.addEventListener("dragleave",()=>{
    uploadForm.classList.remove("border-primary");
});

uploadForm.addEventListener("drop",(e)=>{
    e.preventDefault();
    uploadForm.classList.remove("border-primary");

    const files = e.dataTransfer.files;

    if(!validate_input(files)) return;

    addFilesToQueue(files);
});


/* ---------------- File Select ---------------- */

uploadedPhotos.addEventListener('change', (e) => {

    const files = e.target.files;

    if(!validate_input(files)) return;

    addFilesToQueue(files);

});


function addFilesToQueue(files){

    for(let file of files){

        uploadQueue.push({
            file:file,
            status:"pending",
            retries:0
        });

    }

    totalFiles = uploadQueue.length;
    uploadedFiles = 0;

    selectedPhotos.textContent = "Photos Selected: " + totalFiles;

}


/* ---------------- Submit ---------------- */

uploadForm.addEventListener('submit', (e) => {

    e.preventDefault();

    if(uploadQueue.length === 0){
        notyf.error("Please select photos");
        return;
    }

    const totalCount = total_upload_count + uploadQueue.length;

    if (!isUnlimited && totalCount > 100) {
        document.getElementById("open-subscription-modal").click();
        return;
    }

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

function uploadSingleFile(item){

    

    const formData = new FormData();
    formData.append("upload_data", item.file);

    const sessionSelect = document.getElementById("session-select");

    if(sessionSelect && sessionSelect.value){
        formData.append("session_id",sessionSelect.value);
    }

    const xhr = new XMLHttpRequest();

    

    xhr.onload = function(){

        activeUploads--;
        uploadedFiles++;

        const percent = Math.round((uploadedFiles / totalFiles) * 100);
        const remaining = totalFiles - uploadedFiles;

        progressBar.style.width = percent + "%";
        progressBar.textContent = percent + "%";

        selectedPhotos.textContent =
            `Uploaded ${uploadedFiles} / ${totalFiles} • Remaining ${remaining}`;

        try{

            const response = JSON.parse(xhr.responseText);

            if(xhr.status === 200 && response.upload_success){

                total_upload_count += response.uploaded_images;
                uploadForm.dataset.uploadCount = total_upload_count;

            }else{

                handleUploadError(response,xhr.status,item);

            }

        }catch{

            retryUpload(item);

        }

        if(uploadedFiles === totalFiles){
            notyf.success("All photos uploaded. Processing started.");
        }

        startUploadQueue();

    };

    xhr.onerror = function(){

        activeUploads--;

        retryUpload(item);

        startUploadQueue();

    };

    xhr.open("POST", uploadForm.action, true);

    xhr.setRequestHeader(
        "X-CSRFToken",
        uploadForm.querySelector('[name=csrfmiddlewaretoken]').value
    );

    xhr.send(formData);

}


/* ---------------- Retry ---------------- */

function retryUpload(item){

    if(item.retries < 2){

        item.retries++;

        uploadQueue.push(item);

    }else{

        notyf.error(`Failed to upload ${item.file.name}`);

    }

}


/* ---------------- Error Handler ---------------- */

function handleUploadError(response,statusCode,item){

    if(statusCode === 403 && response.redirect){

        document.getElementById("open-subscription-modal").click();

        document.getElementById("upgrade-plan-btn").onclick = function () {
            window.location.href = response.redirect;
        };

    }else{

        retryUpload(item);

    }

}

});
