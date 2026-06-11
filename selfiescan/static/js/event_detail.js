document.addEventListener("DOMContentLoaded", () => {
    
    const photoGrid = document.getElementById("photo-grid");
    const paginationControls = document.getElementById("pagination-controls");
    const loadingState = document.querySelector('.loading');
    const showPhotos = document.getElementById("show-photo")
    const studioNameInput = document.getElementById("studioNameInput")    
    const eventSection = document.getElementById("event-section");
    const eventId = eventSection.dataset.eventId; //data-event-id converts to eventId camelcase in js 
    const downloadToggle = document.getElementById('download-toggle')
    const toggleFindPhotos = document.getElementById('findPhotosToggle')
    let notyf = new Notyf({ duration: 5000 });

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
