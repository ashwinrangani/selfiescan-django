document.addEventListener("DOMContentLoaded", () => {
    const uploadedPhotos = document.getElementById("upload_data");
    const uploadForm = document.getElementById("upload_photos");
    const selectedPhotos = document.getElementById("selected-photos");
    const progressBarContainer = document.getElementById(
        "progressBarContainer",
    );
    const progressBar = document.getElementById("progressBar");

    let total_upload_count = parseInt(uploadForm.dataset.uploadCount) || 0;
    const isUnlimited = uploadForm.dataset.unlimitedUpload === "true";
    const uploadLimit = parseInt(uploadForm.dataset.uploadLimit || "0");
    const billingURL = uploadForm.dataset.billingUrl;

    const isMobile = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
    const MAX_PARALLEL = isMobile ? 1 : 3;

    let uploadQueue = [];
    let activeUploads = 0;
    let initialTotal = 0;
    let totalFiles = 0;
    let uploadedFiles = 0;
    let failedUploads = 0;
    let subscriptionLimitHit = false;

    const notyf = new Notyf({ duration: 20000, dismissible: true });
    window.addEventListener("offline", () => {
        notyf.error("Internet connection lost");
    });
    window.addEventListener("online", () => {
        notyf.success("Back online");
        if (activeUploads === 0 && uploadQueue.length > 0) {
            isUploading = true;
            document.getElementById("submitBtn").disabled = true;
            progressBarContainer.classList.remove("hidden");
            startUploadQueue();
        }
    });
    window.addEventListener("beforeunload", function (e) {
        if (isUploading || uploadQueue.length > 0 || activeUploads > 0) {
            e.preventDefault();
            e.returnValue = "";
        }
    });

    window.addEventListener("popstate", function () {
        if (isUploading) {
            const confirmLeave = confirm(
                "Uploads are in progress. Are you sure you want to leave?",
            );
            if (!confirmLeave) {
                history.pushState(null, "", location.href);
            }
        }
    });

    // push initial state
    history.pushState(null, "", location.href);

    /* ---------------- Subscription Dialog ---------------- */

    const DIALOG_COPY = {
        limit: {
            title: "Upload limit reached",
            body: "You've reached your 100-photo limit on the free plan. Upgrade to keep uploading.",
        },
        expired: {
            title: "Subscription expired",
            body: "Your plan has expired. Renew it to continue uploading photos.",
        },
        none: {
            title: "No active subscription",
            body: "You need an active subscription to upload photos.",
        },
    };

    function openSubDialog(reason = "limit") {
        const copy = DIALOG_COPY[reason] ?? DIALOG_COPY.limit;
        document.getElementById("sub-dialog-title").textContent = copy.title;
        document.getElementById("sub-dialog-body").textContent = copy.body;
        const backdrop = document.getElementById("sub-dialog-backdrop");
        backdrop.style.display = "flex";
    }
    function closeSubDialog() {
        document.getElementById("sub-dialog-backdrop").style.display = "none";
        subscriptionLimitHit = false;
    }
    document
        .getElementById("sub-dialog-close")
        .addEventListener("click", () => {
            closeSubDialog();
        });

    document
        .getElementById("sub-dialog-dismiss")
        .addEventListener("click", () => {
            closeSubDialog();
        });

    // Close on backdrop click
    document
        .getElementById("sub-dialog-backdrop")
        .addEventListener("click", function (e) {
            if (e.target === this) closeSubDialog();
        });

    document.getElementById("upgrade-plan-btn").onclick = function () {
        if (billingURL) {
            window.location.href = billingURL;
        }
    };

    const ALLOWED_TYPES = [
        "image/jpeg",
        "image/png",
        "image/jpg",
        "image/webp",
        "image/heic",
        "image/heif",
        "image/avif",
    ];
    const ALLOWED_EXTENSIONS = [
        "jpg",
        "jpeg",
        "png",
        "psd",
        "webp",
        "heic",
        "heif",
        "avif",
    ];

    function isValidFile(file) {
        const ext = file.name.split(".").pop().toLowerCase();
        return (
            ALLOWED_TYPES.includes(file.type) ||
            ALLOWED_EXTENSIONS.includes(ext)
        );
    }

    // Prevent browser from opening dropped files
    ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
        document.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    /* ---------------- Drag & Drop ---------------- */
    const dragArea = document.getElementById("drag-area");

    dragArea.addEventListener("dragenter", () =>
        dragArea.classList.add("drag-active"),
    );
    dragArea.addEventListener("dragleave", () =>
        dragArea.classList.remove("drag-active"),
    );
    dragArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        dragArea.classList.add("drag-active");
    });

    dragArea.addEventListener("drop", async (e) => {
        e.preventDefault();
        dragArea.classList.remove("drag-active");

        const items = e.dataTransfer.items;

        let allFiles = [];

        for (let item of items) {
            const entry = item.webkitGetAsEntry();

            if (entry) {
                const files = await readEntry(entry);
                allFiles.push(...files);
            }
        }

        if (!allFiles.length) return;

        addFilesToQueue(allFiles);
    });

    async function readEntry(entry, path = "") {
        if (entry.isFile) {
            return new Promise((resolve, reject) => {
                entry.file(
                    (file) => {
                        // Skip hidden files (dotfiles) and known system files
                        if (
                            file.name.startsWith(".") ||
                            file.name === "Thumbs.db"
                        ) {
                            return resolve([]);
                        }
                        file.fullPath = path + file.name;
                        resolve([file]);
                    },
                    (err) => reject(err),
                );
            });
        }

        if (entry.isDirectory) {
            const reader = entry.createReader();
            const allEntries = [];

            // Keep calling readEntries until it returns an empty batch
            while (true) {
                const batch = await new Promise((resolve, reject) => {
                    reader.readEntries(resolve, reject);
                });

                if (batch.length === 0) break; // done
                allEntries.push(...batch);
            }

            // Recursively resolve all collected entries
            const files = [];
            for (const ent of allEntries) {
                const res = await readEntry(ent, path + entry.name + "/");
                files.push(...res);
            }
            return files;
        }

        return []; // safety: unknown entry type
    }

    /* ---------------- Upload Card ---------------- */
    function createUploadCard(item) {
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
        retryBtn.type = "button";
        retryBtn.textContent = "Retry";

        retryBtn.onclick = function () {
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
    uploadedPhotos.addEventListener("change", (e) => {
        const files = e.target.files;
        addFilesToQueue(files);
        uploadedPhotos.value = "";
    });

    // compress images
    const MAX_COMPRESSION = 3;

    let compressionQueue = [];
    let activeCompressions = 0;

    const toggle = document.getElementById("compress-toggle");
    const options = document.getElementById("compression-options");

    toggle.addEventListener("change", () => {
        options.classList.toggle("hidden", !toggle.checked);
    });

    async function convertHeicToJpeg(file) {
        const ext = file.name.split(".").pop().toLowerCase();
        if (!["heic", "heif"].includes(ext)) return file;

        try {
            const jpegBlob = await heic2any({
                blob: file,
                toType: "image/jpeg",
                quality: 0.92,
            });
            return new File([jpegBlob], file.name.replace(/\.\w+$/, ".jpg"), {
                type: "image/jpeg",
            });
        } catch (err) {
            console.error("HEIC conversion failed:", err);
            return file; // fall back, server will handle it
        }
    }

    function getCompressionOptions() {
        const selected = document.querySelector(
            'input[name="compression"]:checked',
        )?.value;

        switch (selected) {
            case "low":
                return {
                    maxSizeMB: 4,
                    maxWidthOrHeight: 3500,
                    initialQuality: 1,
                };
            case "high":
                return {
                    maxSizeMB: 0.6,
                    maxWidthOrHeight: 1600,
                    initialQuality: 0.7,
                };
            default: // medium
                return {
                    maxSizeMB: 1,
                    maxWidthOrHeight: 2000,
                    initialQuality: 0.8,
                };
        }
    }
    async function compressImage(file) {
        const isEnabled = document.getElementById("compress-toggle").checked;

        // Skip compression if disabled
        if (!isEnabled) return file;
        const ext = file.name.split(".").pop().toLowerCase();
        if (["psd", "avif"].includes(ext)) return file;
        //  Skip small files (important)
        if (file.size < 1.5 * 1024 * 1024) return file;

        const baseOptions = getCompressionOptions();

        const options = {
            ...baseOptions,
            useWebWorker: true,
            preserveExif: true,
        };

        try {
            const compressedBlob = await imageCompression(file, options);

            return new File([compressedBlob], file.name, { type: file.type });
        } catch (err) {
            console.error("Compression failed:", err);
            return file;
        }
    }

    const queuedFileKeys = new Set();

    function getFileKey(file) {
        return `${file.name}-${file.size}`;
    }

    function addFilesToQueue(files) {
        let rejectedCount = 0;

        for (let file of files) {
            if (!isValidFile(file)) {
                rejectedCount++;
                console.warn("Rejected file:", file.name, file.type);
                continue;
            }
            const key = getFileKey(file);
            if (queuedFileKeys.has(key)) {
                console.warn("Duplicate skipped:", file.name);
                continue;
            }
            queuedFileKeys.add(key);
            // create UI instantly
            const item = {
                id: crypto.randomUUID(),
                file: file,
                status: "pending",
                retries: 0,
            };

            createUploadCard(item);
            item.ui.status.textContent = "Queued for compression...";

            // push to compression queue
            compressionQueue.push(item);
        }
        if (rejectedCount > 0) {
            notyf.error(
                `${rejectedCount} file${rejectedCount > 1 ? "s" : ""} skipped — unsupported format.`,
            );
        }
        startCompressionQueue();
    }
    function startCompressionQueue() {
        while (
            activeCompressions < MAX_COMPRESSION &&
            compressionQueue.length
        ) {
            const item = compressionQueue.shift();
            activeCompressions++;

            compressAndQueue(item);
        }
    }
    async function compressAndQueue(item) {
        item.ui.status.textContent = "Compressing...";

        try {
            const ext = item.file.name.split(".").pop().toLowerCase();

            if (["heic", "heif"].includes(ext)) {
                item.ui.status.textContent = "Converting...";
                item.file = await convertHeicToJpeg(item.file);
            }

            const processedFile = await compressImage(item.file);

            item.file = processedFile;

            // update UI
            item.ui.status.textContent = "Ready";
            item.ui.card.querySelector(".item-size").textContent =
                (processedFile.size / (1024 * 1024)).toFixed(1) + " MB";

            //  move to upload queue ONLY (do not start upload)
            uploadQueue.push(item);

            //  update counters
            initialTotal++;
            totalFiles = initialTotal;

            selectedPhotos.textContent = "Photos Selected: " + totalFiles;
        } catch (err) {
            console.error(err);

            failedUploads++;
            item.ui.status.textContent = "Compression failed";
            item.ui.card.classList.add("item-failed");
        }

        activeCompressions--;

        // continue compression queue
        startCompressionQueue();
    }

    /* ---------------- Submit ---------------- */
    let isUploading = false;

    uploadForm.addEventListener("submit", (e) => {
        e.preventDefault();

        if (isUploading) {
            notyf.error("Upload already in progress");
            return;
        }

        if (uploadQueue.length === 0 && activeUploads === 0) {
            notyf.error("Please select photos");
            return;
        }

        const totalCount = total_upload_count + uploadQueue.length;

        if (!isUnlimited && uploadLimit && totalCount > uploadLimit) {
            const status = uploadForm.dataset.subscriptionStatus;
            openSubDialog(
                status === "expired"
                    ? "expired"
                    : status === "none"
                      ? "none"
                      : "limit",
            );
            return;
        }

        isUploading = true;
        document.getElementById("submitBtn").disabled = true;
        progressBarContainer.classList.remove("hidden");
        startUploadQueue();
    });

    /* ---------------- Queue Manager ---------------- */
    function startUploadQueue() {
        while (activeUploads < MAX_PARALLEL && uploadQueue.length) {
            const item = uploadQueue.shift();

            if (item.status === "uploading") continue;

            item.status = "uploading";

            activeUploads++;
            uploadSingleFile(item);
        }
    }

    /* ---------------- Single Upload ---------------- */
    function guessMimeType(filename) {
        const ext = filename.split(".").pop().toLowerCase();
        const map = {
            jpg: "image/jpeg",
            jpeg: "image/jpeg",
            png: "image/png",
            webp: "image/webp",
            heic: "image/heic",
            heif: "image/heif",
            avif: "image/avif",
            psd: "image/vnd.adobe.photoshop",
        };
        return map[ext] || "image/jpeg";
    }

    async function uploadSingleFile(item) {
        item.ui.card.classList.add("item-uploading");
        item.ui.icon.innerHTML = `<span class="icon-[tabler--loader-2] size-3.5 spin"></span>`;

        const csrfToken = uploadForm.querySelector(
            "[name=csrfmiddlewaretoken]",
        ).value;

        const sessionSelect = document.getElementById("session-select");
        const sessionId =
            sessionSelect && sessionSelect.value ? sessionSelect.value : null;

        // Normalize MIME type (CRITICAL FIX)
        const fileType = item.file.type || guessMimeType(item.file.name);
        const fileName = item.file.name;

        try {
            /* ---------------- STEP 1: Get presigned URL ---------------- */
            const presignedRes = await fetch(
                `${uploadForm.dataset.presignedUrl}?file_name=${encodeURIComponent(fileName)}&file_type=${encodeURIComponent(fileType)}`,
            );

            if (!presignedRes.ok) throw new Error("Failed to get upload URL");

            const presignedData = await presignedRes.json();

            /* ---------------- STEP 2: Upload to S3 ---------------- */
            await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                xhr.upload.onprogress = function (e) {
                    if (e.lengthComputable) {
                        const percent = Math.round((e.loaded / e.total) * 100);
                        item.ui.progressBar.style.width = percent + "%";
                        item.ui.status.textContent = percent + "%";
                    }
                };

                xhr.onload = function () {
                    if (xhr.status === 200) {
                        resolve();
                    } else if (xhr.status === 403) {
                        console.error("S3 403 response:", xhr.responseText);
                        reject("Auth error"); // signature mismatch
                    } else {
                        console.error(
                            "S3 error status:",
                            xhr.status,
                            xhr.responseText,
                        );
                        reject("S3 upload failed");
                    }
                };

                xhr.onerror = function () {
                    console.error(
                        "S3 network error — XHR blocked or connection dropped",
                    );
                    reject("S3 upload error");
                };

                xhr.open("PUT", presignedData.url, true);

                // MUST match presigned ContentType exactly
                xhr.setRequestHeader("Content-Type", fileType);
                xhr.send(item.file);
            });

            /* ---------------- STEP 3: Notify Django ---------------- */
            const completeRes = await fetch(
                uploadForm.dataset.uploadCompleteUrl,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken,
                    },
                    body: JSON.stringify({
                        file_key: presignedData.file_key,
                        session_id: sessionId,
                    }),
                },
            );

            if (!completeRes.ok) {
                if (completeRes.status === 403) {
                    const data = await completeRes.json();

                    if (
                        data.message &&
                        data.message.toLowerCase().includes("subscription")
                    ) {
                        if (subscriptionLimitHit) return;
                        subscriptionLimitHit = true;
                        // STOP EVERYTHING
                        uploadQueue = [];
                        isUploading = false;
                        activeUploads = 0;

                        document.getElementById("submitBtn").disabled = false;
                        progressBarContainer.classList.add("hidden");

                        if (data.message.includes("expired")) {
                            openSubDialog("expired");
                        } else if (data.message.includes("No subscription")) {
                            openSubDialog("none");
                        } else {
                            openSubDialog("limit");
                        }
                        return;
                    }
                }

                throw new Error("Backend save failed");
            }

            /* ---------------- SUCCESS ---------------- */
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
            console.error("UPLOAD ERROR:", error);
            notyf.error(`Upload failed: ${error}`);

            activeUploads--;
            item.ui.card.classList.remove("item-uploading");

            item.status = "failed";

            if (error === "Auth error") {
                failedUploads++;

                item.ui.status.textContent = "Auth error";
                item.ui.retryBtn.classList.remove("hidden");
                item.ui.card.classList.add("item-failed");

                item.ui.icon.className = "item-icon";
                item.ui.icon.innerHTML = `<span class="icon-[tabler--lock] size-3.5"></span>`;
            } else {
                retryUpload(item);
            }
        }

        /* ---------------- GLOBAL PROGRESS ---------------- */
        const percent = Math.round((uploadedFiles / totalFiles) * 100);
        const remaining = totalFiles - uploadedFiles;

        progressBar.style.width = percent + "%";
        progressBar.textContent = percent + "%";

        selectedPhotos.textContent = `Uploaded ${uploadedFiles} / ${totalFiles} • Remaining ${remaining}`;

        if (uploadedFiles + failedUploads === totalFiles) {
            isUploading = false;
            queuedFileKeys.clear();
            document.getElementById("submitBtn").disabled = false;

            if (failedUploads === 0) {
                notyf.success("All photos uploaded. Processing started.");
            } else {
                notyf.error(`${failedUploads} uploads failed.`);
            }
        }

        startUploadQueue();
    }

    /* ---------------- Retry ---------------- */
    function retryUpload(item) {
        item.status = "pending";
        if (item.retries < 2) {
            item.retries++;
            item.ui.status.textContent = "Retry " + item.retries + "/2";
            uploadQueue.push(item);
            startUploadQueue();
        } else {
            failedUploads++;
            item.status = "failed";
            item.ui.status.textContent = "Failed";
            item.ui.retryBtn.classList.remove("hidden");
            item.ui.card.classList.add("item-failed");
            item.ui.icon.className = "item-icon";
            item.ui.icon.innerHTML = `<span class="icon-[tabler--circle-x] size-3.5"></span>`;
        }
    }
});
