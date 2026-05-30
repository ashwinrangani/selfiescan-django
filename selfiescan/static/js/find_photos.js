// ── Back Button / LightGallery ───────────────────────────────────────────────
let lgInstanceFind = null;
let lgOpenFind     = false;

window.addEventListener("popstate", function () {
    if (lgOpenFind && lgInstanceFind) {
        try { lgInstanceFind.closeGallery(); } catch (e) {}
        history.pushState({ lgFind: true }, "");
    }
});
// ────────────────────────────────────────────────────────────────────────────


document.addEventListener('DOMContentLoaded', () => {

    // ── Element refs ─────────────────────────────────────────────────────────
    const fileInput      = document.getElementById('selfie');
    const cameraInput    = document.getElementById('camera_selfie');
    const imagePreview   = document.getElementById('image-preview');
    const clearBtn       = document.getElementById('clear-preview');
    const uploadForm     = document.getElementById('upload_selfie');
    const loadingSpinner = document.querySelector('.loading');
    const submitBtn      = document.getElementById('search-btn');
    const dropZone       = document.getElementById('drop-zone');
    const resultsHeader  = document.getElementById('results-header');
    const resultsCount   = document.getElementById('results-count');
    const lgEl           = document.getElementById('lightgallery');
    const messagesEl     = document.querySelector('.messages');

    if (!lgEl) return;

    const isDownloadable =
        lgEl.dataset.eventIsdownload.toLowerCase() === "true";

    // ── Notyf ────────────────────────────────────────────────────────────────
    const notyf = new Notyf({ duration: 5000 });

    // ── Helpers ──────────────────────────────────────────────────────────────
    const ALLOWED = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/psd'];

    function isAllowedType(file) {
        return ALLOWED.includes(file.type);
    }

    function validateInput(input) {
        for (const file of input.files) {
            if (!isAllowedType(file)) {
                notyf.error("Invalid file type. Please upload a photo.");
                input.value = '';
                return false;
            }
        }
        return true;
    }

    function showPreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src          = e.target.result;
            imagePreview.style.display = 'block';
            clearBtn.style.display     = 'flex';
            dropZone?.classList.add('has-preview');
        };
        reader.readAsDataURL(file);
    }

    function clearPreview() {
        fileInput.value  = '';
        cameraInput.value = '';
        fileInput.disabled   = false;
        cameraInput.disabled = false;
        imagePreview.src           = '';
        imagePreview.style.display  = 'none';
        clearBtn.style.display      = 'none';
        dropZone?.classList.remove('has-preview');
    }

    function setLoading(on) {
        if (on) {
            loadingSpinner?.classList.remove('hidden');
            if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Searching…'; }
        } else {
            loadingSpinner?.classList.add('hidden');
            if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Find my photos'; }
        }
    }

    // ── File input events ────────────────────────────────────────────────────
    fileInput?.addEventListener('change', () => {
        if (!validateInput(fileInput)) return;
        if (fileInput.files.length > 0) {
            cameraInput.disabled = true;
            showPreview(fileInput.files[0]);
        }
    });

    cameraInput?.addEventListener('change', () => {
        if (!validateInput(cameraInput)) return;
        if (cameraInput.files.length > 0) {
            fileInput.disabled = true;
            showPreview(cameraInput.files[0]);
        }
    });

    clearBtn?.addEventListener('click', clearPreview);

    // ── Drag and drop ────────────────────────────────────────────────────────
    if (dropZone) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', (e) => {
            // only remove if leaving the zone entirely (not a child element)
            if (!dropZone.contains(e.relatedTarget)) {
                dropZone.classList.remove('drag-over');
            }
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');

            const file = e.dataTransfer?.files?.[0];
            if (!file || !isAllowedType(file)) {
                notyf.error("Please drop an image file.");
                return;
            }

            // Inject into the gallery input
            const dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files       = dt.files;
            cameraInput.disabled  = true;
            showPreview(file);
        });
    }

    // ── LightGallery init ────────────────────────────────────────────────────
    function initLightGallery() {
        if (lgInstanceFind) {
            try { lgInstanceFind.destroy(true); } catch (e) {}
        }

        lgInstanceFind = lightGallery(lgEl, {
            plugins: [lgZoom, lgFullscreen],
            selector: 'a',
            speed: 400,
            licenseKey: '0000-0000-000-0000',
            download: isDownloadable,
            mobileSettings: {
                controls: true,
                showCloseIcon: true,
                download: isDownloadable,
                closeOnTap: false,
            },
        });

        lgEl.addEventListener("lgAfterOpen", () => {
            lgOpenFind = true;
            history.pushState({ lgFind: true }, "");
        });

        lgEl.addEventListener("lgAfterClose", () => {
            lgOpenFind = false;
        });

        lgEl.addEventListener('lgAfterSlide', () => {
            const galleryImg = document.querySelector('.lg-current .lg-img-wrap img');
            if (!galleryImg) return;
            galleryImg.setAttribute('oncontextmenu', isDownloadable ? 'return true;' : 'return false;');
            galleryImg.setAttribute('draggable',     isDownloadable ? 'true'         : 'false');
        });
    }

    // ── Render results ───────────────────────────────────────────────────────
    function renderMatches(matches) {
        lgEl.innerHTML = '';

        matches.forEach(match => {
            const container = document.createElement('div');
            container.className = 'photo-item';

            const anchor = document.createElement('a');
            anchor.href                 = match.medium;
            anchor.dataset.src          = match.medium;
            anchor.dataset.downloadUrl  = match.download;

            const img = document.createElement('img');
            img.src     = match.thumb;
            img.alt     = 'Matched photo';
            img.loading = 'lazy';

            if (!isDownloadable) {
                img.oncontextmenu = () => false;
                img.draggable     = false;
            }

            anchor.appendChild(img);
            container.appendChild(anchor);
            lgEl.appendChild(container);
        });

        initLightGallery();
    }

    // ── Form submit ──────────────────────────────────────────────────────────
    uploadForm?.addEventListener('submit', (e) => {
        e.preventDefault();

        const hasFile = [fileInput, cameraInput]
            .some(inp => inp?.files?.length > 0);

        if (!hasFile) {
            notyf.error("Please select a photo or take a selfie first.");
            return;
        }

        setLoading(true);

        fetch(uploadForm.action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': uploadForm.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            body: new FormData(uploadForm),
        })
        .then(res => {
            if (res.status === 429) throw new Error('busy');
            if (!res.ok)           throw new Error('error');
            return res.json();
        })
        .then(data => {
            setLoading(false);

            const matches = data.matches || [];
            const count   = matches.length;

            if (messagesEl) {
                messagesEl.textContent = count > 0 ? `${count} ${data.message}` : data.message;
            }

            if (resultsHeader) {
                resultsHeader.classList.toggle('visible', count > 0);
                if (resultsCount) resultsCount.textContent = count;
            }

            renderMatches(matches);
        })
        .catch(err => {
            setLoading(false);
            notyf.error(err.message === 'busy'
                ? "Server is busy — please try again shortly."
                : "Something went wrong. Please try again.");
            console.error('find_photos error:', err);
        });
    });

});