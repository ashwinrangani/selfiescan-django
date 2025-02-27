document.addEventListener("DOMContentLoaded", function () {
  const notyf = new Notyf({
    duration: 5000,
    position: { x: "right", y: "bottom" },
    types: [
      {
        type: "info",
        background: "blue",
        icon: false,
      },
    ],
  });

  const messagesScript = document.getElementById("messages-data");

  if (messagesScript) {
    try {
      const messages = JSON.parse(messagesScript.textContent);

      messages.forEach((msg) => {
        if (msg.tags.includes("success")) {
          notyf.success(msg.message);
        } else if (msg.tags.includes("error") || msg.tags.includes("danger")) {
          notyf.error(msg.message);
        } else {
          notyf.success({ type: "info", message: msg.message });
        }
      });
    } catch (error) {
      console.error("Error parsing messages:", error);
    }
  }
});
