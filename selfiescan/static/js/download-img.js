document.addEventListener("DOMContentLoaded", () => {
  const matchesContainer = document.querySelector(".matches-section");
  const fullscreenView = document.getElementById("fullscreen-view");
  const fullscreenImage = document.querySelector("#fullscreen-image .carousel-body");
  const downloadButton = document.getElementById("download-button");
  const closeButton = document.getElementById("close-button");
  const prevButton = document.querySelector(".carousel-prev");
  const nextButton = document.querySelector(".carousel-next");

  let images = [];
  let currentIndex = 0;

  // Show carousel when an image is clicked
  if (matchesContainer) {
    matchesContainer.addEventListener("click", (event) => {
      if (event.target.tagName === "IMG") {
        const clickedImgSrc = event.target.src;

        // Gather all images
        images = Array.from(matchesContainer.querySelectorAll("img")).map(
          (img) => img.src
        );

        // Set the clicked image as the first one
        currentIndex = images.indexOf(clickedImgSrc);

        // Populate the carousel
        fullscreenImage.innerHTML = images
          .map(
            (src, index) => `
              <div class="carousel-slide flex items-center justify-center ${index === currentIndex ? "active" : "hidden"}">
                <img src="${src}" class="size-full object-cover" />
              </div>`
          )
          .join("");

        downloadButton.setAttribute("href", clickedImgSrc);
        downloadButton.setAttribute("download", "image.jpg");

        fullscreenView.classList.remove("hidden");
        fullscreenView.classList.add("flex")
      }
    });
  }

  // Move to the next image
  nextButton.addEventListener("click", () => {
    currentIndex = (currentIndex + 1) % images.length;
    updateCarousel();
  });

  // Move to the previous image
  prevButton.addEventListener("click", () => {
    currentIndex = (currentIndex - 1 + images.length) % images.length;
    updateCarousel();
  });

  // Update carousel display
  function updateCarousel() {
    const slides = document.querySelectorAll(".carousel-slide");
    slides.forEach((slide, index) => {
      slide.classList.toggle("hidden", index !== currentIndex);
    });

    const currentImage = images[currentIndex];
    downloadButton.setAttribute("href", currentImage);
    downloadButton.setAttribute("download", "image.jpg");
  }

  // Close the carousel
  if (closeButton) {
    closeButton.addEventListener("click", () => {
      fullscreenView.classList.add("hidden");
    });
  }

  // Handle download button click
  if (downloadButton) {
    downloadButton.addEventListener("click", () => {
      const link = document.createElement("a");
      link.href = images[currentIndex];
      link.download = "downloaded_image.jpg";
      link.click();
    });
  }
});
