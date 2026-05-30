document.addEventListener("DOMContentLoaded", () => {
    
    const photoGrid = document.getElementById("photo-grid");
    const paginationControls = document.getElementById("pagination-controls");
    const loadingState = document.querySelector('.loading');
    const showPhotos = document.getElementById("show-photo")
    const studioNameInput = document.getElementById("studioNameInput")
    const brandingForm = document.getElementById("branding-form")
    const brandingSwitch = document.getElementById("brandingSwitch");
    const brandingImageInput = document.getElementById("brandingImage");
    const eventSection = document.getElementById("event-section");
    const eventId = eventSection.dataset.eventId; //data-event-id converts to eventId camelcase in js 
    const preview = document.getElementById("branding-logo-preview");      // small thumbnail
    const removeBtn = document.getElementById("remove-branding-logo-btn");
    const startBrandingBtn = document.getElementById("start-branding-btn");
    const downloadToggle = document.getElementById('download-toggle')
    const toggleFindPhotos = document.getElementById('findPhotosToggle')
    let notyf = new Notyf({ duration: 5000 });
// ── Branding — font preview ───────────────────────────────────
    const FONT_STYLES = {
        modern:      "'Montserrat', sans-serif",
        elegant:     "'Cormorant Garamond', serif",
        classic:     "'Playfair Display', serif",
        luxury:      "'Cinzel', serif",
        stylish:     "'Rancho', cursive",
        handwritten: "'Playwrite GB S Guides', cursive",
        ultra_modern:"'Zen Tokyo Zoo', cursive",
    };

    document.querySelectorAll(".font-sample").forEach(el => {
        const style = el.dataset.style;
        if (FONT_STYLES[style]) el.style.fontFamily = FONT_STYLES[style];
    });
    function updateUnifiedPreview() {
    const isLogo = !document.getElementById("logoSection").classList.contains("hidden");
    const opacity = document.getElementById("opacitySlider").value / 100;
    const pos = document.getElementById("brandingPositionInput").value;
    const style = document.getElementById("brandingStyleInput").value;
    const font = document.getElementById("brandingFontInput").value;
    const text = document.getElementById("studioNameInput")?.value || "Studio Name";

    const logoEl = document.getElementById("unifiedLogoPreview");
    const textEl = document.getElementById("unifiedTextPreview");

    // Position mapping
    const positions = {
        bottom_right:  { bottom: "10px", right: "10px", left: "auto",  top: "auto",  transform: "none" },
        bottom_left:   { bottom: "10px", left:  "10px", right: "auto", top: "auto",  transform: "none" },
        bottom_center: { bottom: "10px", left:  "50%",  right: "auto", top: "auto",  transform: "translateX(-50%)" },
        top_right:     { top:    "10px", right: "10px", left: "auto",  bottom: "auto", transform: "none" },
    };
    const p = positions[pos] || positions["bottom_right"];

    if (isLogo) {
        textEl.classList.add("hidden");
        if (logoEl.src && !logoEl.src.endsWith("/")) {
            logoEl.classList.remove("hidden");
        } else {
            logoEl.classList.add("hidden");
        }
        logoEl.style.opacity = opacity;
        Object.assign(logoEl.style, p);
    } else {
    logoEl.classList.add("hidden");
    textEl.classList.remove("hidden");
    textEl.textContent = text;
    textEl.style.opacity = "";          // ← clear element opacity, don't use it for text
    textEl.style.fontFamily = FONT_STYLES[font] || "'Montserrat', sans-serif";
    Object.assign(textEl.style, p);

    if (style === "box") {
        textEl.style.background = `rgba(0,0,0,${(0.25 * opacity).toFixed(2)})`;
        textEl.style.backdropFilter = "blur(4px)";
        textEl.style.webkitBackdropFilter = "blur(4px)";
        textEl.style.borderRadius = "4px";
        textEl.style.color = `rgba(255,255,255,${opacity})`;
    } else {
        textEl.style.background = "transparent";
        textEl.style.backdropFilter = "none";
        textEl.style.webkitBackdropFilter = "none";
        textEl.style.borderRadius = "0";
        textEl.style.color = `rgba(255,255,255,${opacity})`;
    }
}
}

// setType
function setType(t) {
    document.getElementById("logoSection").classList.toggle("hidden", t !== "logo");
    document.getElementById("textSection").classList.toggle("hidden", t !== "text");
    document.getElementById("tabLogo").classList.toggle("btn-primary", t === "logo");
    document.getElementById("tabLogo").classList.toggle("btn-outline", t !== "logo");
    document.getElementById("tabText").classList.toggle("btn-primary", t === "text");
    document.getElementById("tabText").classList.toggle("btn-outline", t !== "text");
    updateUnifiedPreview();
}

// setFont
function setFont(el) {
    document.querySelectorAll(".font-card").forEach(c => {
        c.classList.remove("border-primary", "bg-primary/10");
        c.classList.add("border-base-300");
    });
    el.classList.add("border-primary", "bg-primary/10");
    el.classList.remove("border-base-300");
    document.getElementById("brandingFontInput").value = el.dataset.font;
    updateUnifiedPreview();
}

// setStyle
function setStyle(s) {
    document.getElementById("styleBox").classList.toggle("btn-primary", s === "box");
    document.getElementById("styleBox").classList.toggle("btn-outline", s !== "box");
    document.getElementById("stylePlain").classList.toggle("btn-primary", s === "plain");
    document.getElementById("stylePlain").classList.toggle("btn-outline", s !== "plain");
    document.getElementById("brandingStyleInput").value = s;
    updateUnifiedPreview();
}

// setPos
function setPos(el) {
    document.querySelectorAll(".pos-btn").forEach(b => {
        b.classList.remove("btn-primary");
        b.classList.add("btn-outline");
    });
    el.classList.add("btn-primary");
    el.classList.remove("btn-outline");
    document.getElementById("brandingPositionInput").value = el.dataset.pos;
    updateUnifiedPreview();
}

// opacity slider
document.getElementById("opacitySlider").addEventListener("input", function () {
    document.getElementById("opacityVal").textContent = this.value + "%";
    updateUnifiedPreview();
});

// studio name input
document.getElementById("studioNameInput").addEventListener("input", function () {
    updateUnifiedPreview();
});

// file input
document.getElementById("brandingImage").addEventListener("change", function () {
    const file = this.files[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    preview.src = url;
    preview.classList.remove("hidden");
    document.getElementById("unifiedLogoPreview").src = url;
    updateUnifiedPreview();
});

// initialize on page load
updateUnifiedPreview();


    // ── Branding — wire up controls ───────────────────────────────
    document.getElementById("tabLogo").addEventListener("click", () => setType("logo"));
    document.getElementById("tabText").addEventListener("click", () => setType("text"));

    document.querySelectorAll(".font-card").forEach(el => {
        el.addEventListener("click", () => setFont(el));
    });

    document.getElementById("styleBox").addEventListener("click", () => setStyle("box"));
    document.getElementById("stylePlain").addEventListener("click", () => setStyle("plain"));

    document.querySelectorAll(".pos-btn").forEach(el => {
        el.addEventListener("click", () => setPos(el));
    });



    // ── Branding — enable/disable toggle ─────────────────────────
    brandingSwitch.addEventListener("change", function () {
        const isEnabled = this.checked;
        document.querySelectorAll(
            "#branding-form input:not(#brandingSwitch), #branding-form button:not(#branding-btn)"
        ).forEach(el => { el.disabled = !isEnabled; });

        ["#logoSection", "#textSection"].forEach(sel => {
            const el = document.querySelector(sel);
            if (el) {
                el.style.opacity = isEnabled ? "1" : "0.4";
                el.style.pointerEvents = isEnabled ? "" : "none";
            }
        });
    });

    // ── Branding — initialize on page load ────────────────────────
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

    // ── Branding — form submit ────────────────────────────────────
    brandingForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const formData = new FormData(brandingForm);
        const isText = !document.getElementById("logoSection").classList.contains("hidden") === false;
        formData.set("branding_enabled", brandingSwitch.checked);
        formData.set("branding_type", document.getElementById("textSection").classList.contains("hidden") ? "logo" : "text");

        fetch(`/event/${eventId}/branding/`, {
            method: "POST",
            headers: { "X-CSRFToken": formData.get("csrfmiddlewaretoken") },
            body: formData,
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (data.logo_url) {
                    preview.src = data.logo_url;
                    preview.classList.remove("hidden");
                    removeBtn.classList.remove("hidden");
                    brandingImageInput.value = "";
                    setType("logo");
                } else {
                    preview.src = "";
                    preview.classList.add("hidden");
                    removeBtn.classList.add("hidden");
                    setType("text");
                }
                notyf.success("Branding updated successfully!");
            } else {
                notyf.error("Something went wrong while updating branding.");
            }
        })
        .catch(() => notyf.error("An error occurred."));
    });

    // ── Branding — remove logo ────────────────────────────────────
    if (removeBtn) {
    removeBtn.addEventListener("click", function () {
        fetch(`/event/${eventId}/branding/remove-logo/`, {
            method: "POST",
            headers: { "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value },
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                notyf.success("Branding logo removed!");
                preview.src = "";
                preview.classList.add("hidden");
                removeBtn.classList.add("hidden");

                // Update unified logo preview
                const unifiedLogo = document.getElementById("unifiedLogoPreview");
                if (unifiedLogo) {
                    unifiedLogo.src = "";
                    unifiedLogo.classList.add("hidden");
                }

                setType(data.branding_text ? "text" : "logo");
                updateUnifiedPreview();
            } else {
                notyf.error("Failed to remove branding logo.");
            }
        })
        .catch((err) => {
            console.error("Remove logo error:", err);
            notyf.error("Something went wrong removing the logo.");
        });
    });
}

    // ── Branding — start branding ─────────────────────────────────
    startBrandingBtn.addEventListener("click", () => {
        startBrandingBtn.disabled = true;
        fetch(`/event/${eventId}/start-branding/`, {
            method: "POST",
            headers: { "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value },
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                notyf.success(data.message);
            } else {
                notyf.error(data.message || "Failed to start branding.");
            }
            startBrandingBtn.disabled = false;
        })
        .catch(() => {
            notyf.error("Error starting branding.");
            startBrandingBtn.disabled = false;
        });
    });


// Handle toggle enable/disable for find photos
toggleFindPhotos.addEventListener('change', function(){
  const eventId = this.getAttribute('data-event-id');
  
  const is_enabled = this.checked;
  console.log(is_enabled)
  fetch(`/events/${eventId}/toggle-find-photos/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value,
      'X-requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({ is_enabled: is_enabled})
  })
  .then(response => response.json())
  .then(data => {
    if (data.success){
      notyf.success(data.message)
    } else {
      notyf.error(data.message);
      this.checked = !is_enabled
    }
  })
  .catch(error => {
    notyf.error('An error occured while updating the enable/disable setting.');
    this.checked = !is_enabled
  })
});

//Handle download toggle for find photos
downloadToggle.addEventListener('change', function(){
  const eventId = this.getAttribute('data-event-id');
  
  const is_downloadable = this.checked;
  console.log(is_downloadable)
  fetch(`/events/${eventId}/toggle-download/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value,
      'X-requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({ is_downloadable: is_downloadable})
  })
  .then(response => response.json())
  .then(data => {
    if (data.success){
      notyf.success(data.message)
    } else {
      notyf.error(data.message);
      this.checked = !is_downloadable
    }
  })
  .catch(error => {
    notyf.error('An error occured while updating the download setting.');
    this.checked = !is_downloadable
  })
})

// photo grid of the event photos
let lgInstance = null;
let lgOpen = false;  // track if gallery is open

function initLightGallery() {
  const lightGalleryElement = document.getElementById('lightgallery');
  if (lightGalleryElement) {
    // destroy previous instance if exists (important for AJAX pagination)
    if (lgInstance) {
      try { lgInstance.destroy(true); } catch (e) {}
    }

    lgInstance = lightGallery(lightGalleryElement, {
      plugins: [lgZoom, lgFullscreen],
      selector: 'a',
      speed: 400,
      licenseKey: '0000-0000-000-0000',
      download: true,
      numberOfSlideItemsInDom: 12,

      mobileSettings: {
        controls: true,
        showCloseIcon: true,
        download: true,
        closeOnTap: false,
      },
    });

    // === BACK BUTTON FIX ===
    lightGalleryElement.addEventListener("lgAfterOpen", () => {
      lgOpen = true;
      history.pushState({ lg: true }, ""); // fake history entry
    });

    lightGalleryElement.addEventListener("lgAfterClose", () => {
      lgOpen = false;
    });
  }
}

// Handle browser back button
window.addEventListener("popstate", function (event) {
  if (lgOpen && lgInstance) {
    lgInstance.closeGallery();
    history.pushState({ lg: true }, ""); // re-add fake state so next back press works
  }
});

initLightGallery()
  if (!photoGrid || !paginationControls) {
    console.error("Error: photo-grid or pagination-controls not found!");
    return;
  }

  if (showPhotos) {
    showPhotos.addEventListener('click', () => {
      photoGrid.style.display = 'block';
      paginationControls.style.display = 'block';
      
    });
  }

  paginationControls.addEventListener("click", (e) => {
    if (e.target.classList.contains("page-link")) {
      const page = e.target.getAttribute("data-page");
      loadingState.style.display = "block";

      fetch(`/event/${eventId}/photos/?page=${page}`)
        .then((response) => {
          if (!response.ok) throw new Error(`Failed to load page ${page}`);
          return response.json();
        })
        .then((data) => {
          loadingState.style.display = "none";

          if (data.html && data.pagination_html) {
            photoGrid.innerHTML = data.html;
            paginationControls.innerHTML = data.pagination_html;
            initLightGallery()
            window.scrollTo({ top: photoGrid.offsetTop - 100, behavior: "smooth" });
          } else {
            console.error("Error: Incomplete data received", data);
          }
        })
        .catch((error) => console.error("Error loading photos:", error));
    }
  });

 // ---- DELETE SELECTED PHOTOS LOGIC ---- //

const selectAllBtn = document.getElementById("select-all");
const deselectAllBtn = document.getElementById("deselect-all");
const deleteSelectedBtn = document.getElementById("delete-selected");
const photoActionBar = document.getElementById("photo-action-bar");

function getSelectedPhotoIds() {
  return Array.from(document.querySelectorAll('input[name="photo_ids"]:checked'))
              .map(cb => cb.value);
}

function updateActionBarVisibility() {
  const anyChecked = getSelectedPhotoIds().length > 0;
  photoActionBar.classList.toggle("hidden", !anyChecked);

}

document.addEventListener("change", (e) => {
 if (e.target.name === "photo_ids") {
    const photoItem = e.target.closest(".photo-item");
    if (e.target.checked) {
      photoItem.classList.add("selected");
    } else {
      photoItem.classList.remove("selected");
    }
    updateActionBarVisibility();
  }
});

if (selectAllBtn) {
  selectAllBtn.addEventListener("click", () => {
  document.querySelectorAll('input[name="photo_ids"]').forEach(cb => {
    cb.checked = true;
    cb.closest(".photo-item").classList.add("selected");
  });
  updateActionBarVisibility();
});
}

if (deselectAllBtn) {
  deselectAllBtn.addEventListener("click", () => {
  document.querySelectorAll('input[name="photo_ids"]').forEach(cb => {
    cb.checked = false;
    cb.closest(".photo-item").classList.remove("selected");
  });
  updateActionBarVisibility();
});
}

if (deleteSelectedBtn) {
  deleteSelectedBtn.addEventListener("click", () => {
    const selectedIds = getSelectedPhotoIds();
    if (selectedIds.length === 0) {
      notyf.error("No photos selected!");
      return;
    }

    if (!confirm(`Delete ${selectedIds.length} selected photo(s)?`)) return;

    fetch(`/event/${eventId}/delete-selected/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value,
      },
      body: JSON.stringify({ photo_ids: selectedIds }),
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          notyf.success(data.message);
          // Remove deleted photos from DOM
          selectedIds.forEach(id => {
            const photoDiv = document.querySelector(`input[value="${id}"]`)?.closest("div");
            if (photoDiv){
            photoDiv.classList.add("opacity-0", "scale-95", "transition", "duration-300");
            setTimeout(() => photoDiv.remove(), 300);
            } 
           });
          updateActionBarVisibility(); 
        } else {
          notyf.error(data.message || "Failed to delete selected photos.");
        }
      })
      .catch(err => {
        console.error("Delete Error:", err);
        notyf.error("An error occurred while deleting photos.");
      });
  });
}


});
