document.addEventListener("DOMContentLoaded", () => {
  const matchesContainer = document.querySelector(".matches-section");
  const fullscreenView = document.getElementById("fullscreen-view");
  const fullscreenImage = document.getElementById("fullscreen-image");
  const downloadButton = document.getElementById("download-button");
  const closeButton = document.getElementById("close-button");

  if (matchesContainer) {
    matchesContainer.addEventListener("click", (event) => {
      if (event.target.tagName === "IMG") {
        console.log("clicked");
        const imgSrc = event.target.src;
        fullscreenImage.src = imgSrc;
        downloadButton.setAttribute("href", imgSrc); // Set download link
        downloadButton.setAttribute("download", "image.jpg");
        fullscreenView.classList.remove("hidden");
      }
    });
  }

  if (downloadButton) {
    downloadButton.addEventListener("click", () => {
      const link = document.createElement("a");
      link.href = fullscreenImage.src;
      link.download = "downloaded_image.jpg";
      link.click();
    });
  }

  if (closeButton) {
    closeButton.addEventListener("click", () => {
      fullscreenView.classList.add("hidden");
      fullscreenImage.src = "";
    });
  }
});
