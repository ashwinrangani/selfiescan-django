document.addEventListener("DOMContentLoaded", function () {

    // ── Refs ──────────────────────────────────────────────────────
    const brandingSection = document.getElementById("branding-section");
    const eventId         = brandingSection.dataset.eventId;
    const existingLogoUrl = brandingSection.dataset.logoUrl;
    const brandingForm       = document.getElementById("branding-form");
    const brandingSwitch     = document.getElementById("brandingSwitch");
    const brandingImageInput = document.getElementById("brandingImage");
    const studioNameInput    = document.getElementById("studioNameInput");
    const preview            = document.getElementById("branding-logo-preview");
    const removeBtn          = document.getElementById("remove-branding-logo-btn");
    const startBrandingBtn   = document.getElementById("start-branding-btn");
    const canvas             = document.getElementById("brandingCanvas");
    const ctx                = canvas.getContext("2d");
    const placeholder        = document.getElementById("canvasPlaceholder");
    const notyf              = new Notyf({ duration: 5000 });

    // ── Canvas setup ──────────────────────────────────────────────
    const CANVAS_W = 800;
    const CANVAS_H = 533;
    canvas.width  = CANVAS_W;
    canvas.height = CANVAS_H;

    // State
    let logoImage = null;   // loaded Image object for logo
    

    // ── Font map ──────────────────────────────────────────────────
    const FONT_STYLES = {
        modern:      "Montserrat",
        elegant:     "Cormorant Garamond",
        classic:     "Playfair Display",
        luxury:      "Cinzel",
        stylish:     "Rancho",
        handwritten: "Playwrite GB S Guides",
        ultra_modern:"Zen Tokyo Zoo",
    };

    // Apply font family to font card samples
    document.querySelectorAll(".font-sample").forEach(el => {
        const style = el.dataset.style;
        if (FONT_STYLES[style]) el.style.fontFamily = `'${FONT_STYLES[style]}', sans-serif`;
    });

    // ── Draw gradient background ──────────────────────────────────
    function drawBackground() {
        const grad = ctx.createLinearGradient(0, 0, CANVAS_W, CANVAS_H);
        grad.addColorStop(0,    "#667eea");
        grad.addColorStop(0.5,  "#764ba2");
        grad.addColorStop(1,    "#f093fb");
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);
    }
    // ── Sample photos state ──────────────────────────────────────
let sampleImages = [];      // loaded Image objects
let currentSampleIndex = 0;

// Draw an image covering the full canvas (like CSS object-fit: cover)
function drawImageCover(img, canvasW, canvasH) {
    const imgRatio    = img.naturalWidth / img.naturalHeight;
    const canvasRatio = canvasW / canvasH;
    let sx, sy, sw, sh;

    if (imgRatio > canvasRatio) {
        sh = img.naturalHeight;
        sw = sh * canvasRatio;
        sx = (img.naturalWidth - sw) / 2;
        sy = 0;
    } else {
        sw = img.naturalWidth;
        sh = sw / canvasRatio;
        sx = 0;
        sy = (img.naturalHeight - sh) / 2;
    }
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, canvasW, canvasH);
}

    // ── Main canvas render ────────────────────────────────────────
    // ── Sample photos state ──────────────────────────────────────

// Draw an image covering the full canvas (like CSS object-fit: cover)
function drawImageCover(img, canvasW, canvasH) {
    const imgRatio    = img.naturalWidth / img.naturalHeight;
    const canvasRatio = canvasW / canvasH;
    let sx, sy, sw, sh;

    if (imgRatio > canvasRatio) {
        sh = img.naturalHeight;
        sw = sh * canvasRatio;
        sx = (img.naturalWidth - sw) / 2;
        sy = 0;
    } else {
        sw = img.naturalWidth;
        sh = sw / canvasRatio;
        sx = 0;
        sy = (img.naturalHeight - sh) / 2;
    }
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, canvasW, canvasH);
}

// Update renderCanvas's background section
function renderCanvas() {
    ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);

    if (sampleImages.length > 0) {
        drawImageCover(sampleImages[currentSampleIndex], CANVAS_W, CANVAS_H);
    } else {
        drawBackground();
    }

    placeholder.style.display = "none";

    const isLogo  = !document.getElementById("logoSection").classList.contains("hidden");
    const opacity = document.getElementById("opacitySlider").value / 100;
    const pos     = document.getElementById("brandingPositionInput").value;
    const style   = document.getElementById("brandingStyleInput").value;
    const fontKey = document.getElementById("brandingFontInput").value;
    const text    = studioNameInput?.value?.trim() || "Studio Name";
    const margin  = 20;

    if (isLogo) {
        if (!logoImage) return;
        drawLogo(logoImage, pos, opacity, margin);
    } else {
        if (style === "diagonal") {
            drawDiagonalText(text, fontKey, opacity);
        } else {
            drawPositionedText(text, fontKey, style, pos, opacity, margin);
        }
    }
}

// ── Load sample photos button ─────────────────────────────────
document.getElementById("loadSamplePhotosBtn").addEventListener("click", function () {
    const btn = this;
    btn.disabled = true;
    btn.innerHTML = `<span class="icon-[tabler--loader-2] size-4 animate-spin"></span> Loading...`;

    fetch(`/event/${eventId}/branding-sample-photos/`)
        .then(res => res.json())
        .then(data => {
            if (!data.photos || data.photos.length === 0) {
                notyf.error("No processed photos found yet.");
                btn.disabled = false;
                btn.innerHTML = `<span class="icon-[tabler--photo] size-4"></span> Use My Photos`;
                return;
            }

            let loaded = 0;
            sampleImages = [];
            data.photos.forEach((url, i) => {
                const img = new Image();
                img.onload = () => {
                    sampleImages[i] = img;
                    loaded++;
                    if (loaded === data.photos.length) {
                        currentSampleIndex = 0;
                        renderCanvas();
                        updateSampleNav();
                        document.getElementById("sampleNav").classList.remove("hidden");
                        document.getElementById("sampleNav").classList.add("flex");
                        btn.innerHTML = `<span class="icon-[tabler--refresh] size-4"></span> Refresh Photos`;
                        btn.disabled = false;
                    }
                };
                img.onerror = () => {
                    loaded++;
                    if (loaded === data.photos.length && sampleImages.filter(Boolean).length > 0) {
                        sampleImages = sampleImages.filter(Boolean);
                        currentSampleIndex = 0;
                        renderCanvas();
                        updateSampleNav();
                        document.getElementById("sampleNav").classList.remove("hidden");
                        document.getElementById("sampleNav").classList.add("flex");
                    }
                    btn.disabled = false;
                    btn.innerHTML = `<span class="icon-[tabler--refresh] size-4"></span> Refresh Photos`;
                };
                img.src = url;
            });
        })
        .catch(() => {
            notyf.error("Failed to load photos.");
            btn.disabled = false;
            btn.innerHTML = `<span class="icon-[tabler--photo] size-4"></span> Use My Photos`;
        });
});

function updateSampleNav() {
    document.getElementById("sampleCounter").textContent =
        `${currentSampleIndex + 1} / ${sampleImages.length}`;
}

document.getElementById("samplePrevBtn").addEventListener("click", () => {
    if (sampleImages.length === 0) return;
    currentSampleIndex = (currentSampleIndex - 1 + sampleImages.length) % sampleImages.length;
    updateSampleNav();
    renderCanvas();
});

document.getElementById("sampleNextBtn").addEventListener("click", () => {
    if (sampleImages.length === 0) return;
    currentSampleIndex = (currentSampleIndex + 1) % sampleImages.length;
    updateSampleNav();
    renderCanvas();
});

    // ── Draw logo ─────────────────────────────────────────────────
    function drawLogo(img, pos, opacity, margin) {
        // Scale logo to max 20% width or 15% height
        const maxW = CANVAS_W * 0.20;
        const maxH = CANVAS_H * 0.15;
        let w = img.naturalWidth;
        let h = img.naturalHeight;

        const scale = Math.min(maxW / w, maxH / h, 1);
        w = Math.round(w * scale);
        h = Math.round(h * scale);

        const { x, y } = calcPosition(pos, w, h, margin);

        ctx.save();
        ctx.globalAlpha = opacity;
        ctx.drawImage(img, x, y, w, h);
        ctx.restore();
    }

    // ── Draw positioned text (box or plain) ───────────────────────
    function drawPositionedText(text, fontKey, style, pos, opacity, margin) {
        const fontName = FONT_STYLES[fontKey] || "Montserrat";
        const fontSize = Math.round(CANVAS_W * 0.025);  // ~2.5% of width
        ctx.font = `${fontSize}px '${fontName}'`;

        const metrics  = ctx.measureText(text);
        const tw       = metrics.width;
        const th       = fontSize;
        const padX     = 14;
        const padY     = 8;
        const boxW     = tw + padX * 2;
        const boxH     = th + padY * 2;

        const { x, y } = calcPosition(pos, boxW, boxH, margin);
        const tx = x + padX;
        const ty = y + padY + th * 0.8; // baseline offset

        if (style === "box") {
            // Frosted glass effect — blur the region
            ctx.save();
            ctx.globalAlpha = opacity * 0.35;
            ctx.fillStyle   = "rgba(0,0,0,1)";
            ctx.beginPath();
            ctx.roundRect(x, y, boxW, boxH, 4);
            ctx.fill();
            ctx.restore();
        }

        // Text
        ctx.save();
        ctx.globalAlpha = opacity;
        ctx.fillStyle   = "white";
        ctx.font        = `${fontSize}px '${fontName}'`;
        ctx.fillText(text, tx, ty);
        ctx.restore();
    }

    // ── Draw diagonal tiled text ──────────────────────────────────
    function drawDiagonalText(text, fontKey, opacity) {
        const fontName = FONT_STYLES[fontKey] || "Montserrat";
        const fontSize = Math.round(CANVAS_W * 0.03);
        ctx.font = `${fontSize}px '${fontName}'`;

        const metrics   = ctx.measureText(text);
        const tw        = metrics.width;
        const th        = fontSize;
        const spacingX  = tw + 80;
        const spacingY  = th + 60;
        const numLines  = 3;
        const angle     = Math.atan2(CANVAS_H, CANVAS_W);

        ctx.save();
        ctx.globalAlpha = opacity;
        ctx.fillStyle   = "white";
        ctx.translate(CANVAS_W / 2, CANVAS_H / 2);
        ctx.rotate(-angle);

        const diagonal = Math.sqrt(CANVAS_W ** 2 + CANVAS_H ** 2);
        const startY   = -(diagonal / 2);
        const lineGap  = diagonal / (numLines + 1);

        for (let i = 0; i < numLines; i++) {
            const ly = startY + lineGap * (i + 1);
            const xOffset = i % 2 === 1 ? spacingX / 2 : 0;
            for (let lx = -diagonal; lx < diagonal; lx += spacingX) {
                ctx.fillText(text, lx + xOffset, ly);
            }
        }

        ctx.restore();
    }

    // ── Position helper ───────────────────────────────────────────
    function calcPosition(pos, elW, elH, margin) {
        const positions = {
            bottom_right:  { x: CANVAS_W - elW - margin, y: CANVAS_H - elH - margin },
            bottom_left:   { x: margin,                  y: CANVAS_H - elH - margin },
            bottom_center: { x: (CANVAS_W - elW) / 2,   y: CANVAS_H - elH - margin },
            top_right:     { x: CANVAS_W - elW - margin, y: margin },
        };
        return positions[pos] || positions["bottom_right"];
    }

    // ── Type tabs ─────────────────────────────────────────────────
    function setType(t) {
        document.getElementById("logoSection").classList.toggle("hidden", t !== "logo");
        document.getElementById("textSection").classList.toggle("hidden", t !== "text");

        const tabLogo = document.getElementById("tabLogo");
        const tabText = document.getElementById("tabText");
        const active   = ["bg-base-100", "text-primary", "shadow-sm", "font-semibold"];
        const inactive = ["text-base-content/60"];

        if (t === "logo") {
            tabLogo.classList.add(...active);
            tabLogo.classList.remove(...inactive);
            tabText.classList.remove(...active);
            tabText.classList.add(...inactive);
        } else {
            tabText.classList.add(...active);
            tabText.classList.remove(...inactive);
            tabLogo.classList.remove(...active);
            tabLogo.classList.add(...inactive);
        }
        renderCanvas();
    }

    // ── Font cards ────────────────────────────────────────────────
    function setFont(el) {
        document.querySelectorAll(".font-card").forEach(c => {
            c.classList.remove("border-primary", "bg-primary/10");
            c.classList.add("border-base-300");
        });
        el.classList.add("border-primary", "bg-primary/10");
        el.classList.remove("border-base-300");
        document.getElementById("brandingFontInput").value = el.dataset.font;
        renderCanvas();
    }

    // ── Text style ────────────────────────────────────────────────
    function setStyle(s) {
        ["styleBox", "stylePlain", "styleDiagonal"].forEach(id => {
            const btn = document.getElementById(id);
            const isActive = (id === `style${s.charAt(0).toUpperCase() + s.slice(1)}`);
            btn.classList.toggle("btn-primary", isActive);
            btn.classList.toggle("btn-outline", !isActive);
        });
        document.getElementById("brandingStyleInput").value = s;
        renderCanvas();
    }

    // ── Position ──────────────────────────────────────────────────
    function setPos(el) {
        document.querySelectorAll(".pos-btn").forEach(b => {
            b.classList.remove("btn-primary");
            b.classList.add("btn-outline");
        });
        el.classList.add("btn-primary");
        el.classList.remove("btn-outline");
        document.getElementById("brandingPositionInput").value = el.dataset.pos;
        renderCanvas();
    }

    // ── Wire up controls ──────────────────────────────────────────
    document.getElementById("tabLogo").addEventListener("click", () => setType("logo"));
    document.getElementById("tabText").addEventListener("click", () => setType("text"));

    document.querySelectorAll(".font-card").forEach(el => {
        el.addEventListener("click", () => setFont(el));
    });

    document.getElementById("styleBox").addEventListener("click",      () => setStyle("box"));
    document.getElementById("stylePlain").addEventListener("click",    () => setStyle("plain"));
    document.getElementById("styleDiagonal").addEventListener("click", () => setStyle("diagonal"));

    document.querySelectorAll(".pos-btn").forEach(el => {
        el.addEventListener("click", () => setPos(el));
    });

    document.getElementById("opacitySlider").addEventListener("input", function () {
        document.getElementById("opacityVal").textContent = this.value + "%";
        renderCanvas();
    });

    studioNameInput?.addEventListener("input", renderCanvas);

    // ── File input — load logo image ──────────────────────────────
    brandingImageInput.addEventListener("change", function () {
        const file = this.files[0];
        if (!file) return;
        const url = URL.createObjectURL(file);

        // Update small thumbnail
        if (preview) {
            preview.src = url;
            preview.classList.remove("hidden");
        }
        if (removeBtn) removeBtn.classList.remove("hidden");

        const img = new Image();
        img.onload = () => {
            logoImage = img;
            renderCanvas();
        };
        img.src = url;
    });

    // ── Load existing logo on page load ───────────────────────────
    if (existingLogoUrl) {
    const existingLogo = new Image();
        existingLogo.onload = () => {
        logoImage = existingLogo;
        renderCanvas();
    };
    existingLogo.onerror = () => {
        renderCanvas();
    };
    existingLogo.src = existingLogoUrl;
} else {
    renderCanvas();
}

 

    // ── Branding switch ───────────────────────────────────────────
    brandingSwitch.addEventListener("change", function () {
        const isEnabled = this.checked;
        document.querySelectorAll(
            "#branding-form input:not(#brandingSwitch), #branding-form button:not(#branding-btn)"
        ).forEach(el => { el.disabled = !isEnabled; });
        ["#logoSection", "#textSection"].forEach(sel => {
            const el = document.querySelector(sel);
            if (el) {
                el.style.opacity      = isEnabled ? "1" : "0.4";
                el.style.pointerEvents = isEnabled ? "" : "none";
            }
        });
    });

    // ── Init on page load ─────────────────────────────────────────
    const hasText = studioNameInput && studioNameInput.value.trim().length > 0;
    setType(hasText ? "text" : "logo");

    if (!brandingSwitch.checked) {
        document.querySelectorAll(
            "#branding-form input:not(#brandingSwitch), #branding-form button:not(#branding-btn)"
        ).forEach(el => { el.disabled = true; });
        ["#logoSection", "#textSection"].forEach(sel => {
            const el = document.querySelector(sel);
            if (el) { el.style.opacity = "0.4"; el.style.pointerEvents = "none"; }
        });
    }

    // Draw initial canvas
    renderCanvas();

    // ── Form submit ───────────────────────────────────────────────
    brandingForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const formData = new FormData(brandingForm);
        formData.set("branding_enabled", brandingSwitch.checked);
        formData.set("branding_type",
            document.getElementById("textSection").classList.contains("hidden") ? "logo" : "text"
        );

        fetch(`/event/${eventId}/branding/`, {
            method: "POST",
            headers: { "X-CSRFToken": document.querySelector("#branding-form input[name='csrfmiddlewaretoken']").value },
            body: formData,
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (data.logo_url) {
                    preview.src = data.logo_url;
                preview.classList.remove("hidden");

                // ── unhide the parent row too ──
                const previewRow = document.getElementById("logo-preview-row");
                if (previewRow) {
                    previewRow.classList.remove("hidden");
                    previewRow.classList.add("flex");
                }

                if (removeBtn) removeBtn.classList.remove("hidden");
                brandingImageInput.value = "";
                setType("logo");

    
                } else {
                    if (preview) { preview.src = ""; preview.classList.add("hidden"); }
                    if (removeBtn) removeBtn.classList.add("hidden");
                    logoImage = null;
                    setType("text");
                }
                notyf.success("Branding settings saved!");
                // Only refresh the badge, not the progress box
                fetch(`/event/${eventId}/branding-status/`)
                    .then(res => res.json())
                    .then(statusData => updateBadge(statusData))
                    .catch(() => {});
            } else {
                notyf.error(data.error || "Failed to save settings.");
            }
        })
        .catch(() => notyf.error("An error occurred."));
    });

    // ── Remove logo ───────────────────────────────────────────────
    if (removeBtn) {
        removeBtn.addEventListener("click", () => {
            fetch(`/event/${eventId}/branding/remove-logo/`, {
                method: "POST",
                headers: { "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value },
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    notyf.success("Logo removed!");
                    if (preview) { preview.src = ""; preview.classList.add("hidden"); }
                    removeBtn.classList.add("hidden");
                    logoImage = null;
                    setType(data.branding_text ? "text" : "logo");
                    renderCanvas();
                } else {
                    notyf.error("Failed to remove logo.");
                }
            })
            .catch(() => notyf.error("Something went wrong."));
        });
    }

    // ── Branding status polling ───────────────────────────────────
    let brandingPollInterval = null;

    function fetchBrandingStatus() {
        fetch(`/event/${eventId}/branding-status/`)
            .then(res => res.json())
            .then(data => updateBrandingStatusUI(data))
            .catch(err => console.error("Branding status error:", err));
    }

    function updateBadge(data) {
    const badge = document.getElementById("unbrandedBadge");
    if (!badge) return;
    if (!data.complete && data.pending > 0) {
        badge.textContent = `${data.pending} pending`;
        badge.classList.remove("hidden");
    } else {
        badge.classList.add("hidden");
    }
}

function updateBrandingStatusUI(data) {
    updateBadge(data);

    const box   = document.getElementById("brandingStatusBox");
    const text  = document.getElementById("brandingStatusText");
    const bar   = document.getElementById("brandingProgressBar");
    const label = document.getElementById("brandingStatusLabel");

    if (!data.branding_enabled || data.total === 0) {
        box.classList.add("hidden");
        stopBrandingPoll();
        return;
    }

    const pct = Math.round((data.branded / data.total) * 100);
    text.textContent = `${data.branded} / ${data.total}`;
    bar.style.width  = `${pct}%`;

    if (data.complete) {
        bar.classList.remove("bg-primary");
        bar.classList.add("bg-success");
        label.textContent = "All photos branded ✓";
        label.classList.remove("text-error");
        label.classList.add("text-success");
        box.classList.remove("hidden");
        stopBrandingPoll();
        startBrandingBtn.disabled = false;
        document.getElementById("branding-btn").disabled = false;
        notyf.success("Branding complete!");
        setTimeout(() => box.classList.add("hidden"), 8000);
    } else {
        box.classList.remove("hidden");
        bar.classList.remove("bg-success");
        bar.classList.add("bg-primary");
        label.textContent = `${data.pending} photo${data.pending > 1 ? "s" : ""} processing...`;
        label.classList.remove("text-error", "text-success");
    }
}

    function startBrandingPoll() {
        if (brandingPollInterval) return;
        brandingPollInterval = setInterval(fetchBrandingStatus, 4000);
    }

    function stopBrandingPoll() {
        clearInterval(brandingPollInterval);
        brandingPollInterval = null;
    }

    // Page load init
fetch(`/event/${eventId}/branding-status/`)
    .then((res) => res.json())
    .then((data) => {
        // Always update badge
        updateBadge(data);
        
        
        const inProgress =
            data.branding_enabled &&
            data.total > 0 &&
            data.branded > 0 &&
            !data.complete;

        if (inProgress) {
            updateBrandingStatusUI(data);
            startBrandingBtn.disabled = true;
            document.getElementById("branding-btn").disabled = true;
            startBrandingPoll();
        }
    })
    .catch((err) => console.error("Branding status init error:", err));

    // Start branding button
    startBrandingBtn.addEventListener("click", () => {
        startBrandingBtn.disabled = true;
        document.getElementById("branding-btn").disabled = true;

        fetch(`/event/${eventId}/start-branding/`, {
            method: "POST",
            headers: { "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value },
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                notyf.success(data.message);
                fetchBrandingStatus();
                startBrandingPoll();
            } else {
                notyf.error(data.message || "Failed to start branding.");
                startBrandingBtn.disabled = false;
                document.getElementById("branding-btn").disabled = false;
            }
        })
        .catch(() => {
            notyf.error("Error starting branding.");
            startBrandingBtn.disabled = false;
            document.getElementById("branding-btn").disabled = false;
        });
    });

});