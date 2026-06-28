(async function hydrateCsrfToken(){
    const isStaticPreview = window.location.protocol === "file:" || window.location.pathname.endsWith(".html");
    const staticForms = document.querySelectorAll("form[data-static-redirect]");

    if (isStaticPreview) {
        staticForms.forEach((form) => {
            form.addEventListener("submit", (event) => {
                event.preventDefault();
                window.location.href = form.dataset.staticRedirect;
            });
        });
    }

    const alerts = document.getElementById("formAlerts");
    const params = new URLSearchParams(window.location.search);
    const message = params.get("error") || params.get("notice");

    if (alerts && message) {
        alerts.hidden = false;
        alerts.innerHTML = "";

        const item = document.createElement("p");
        item.className = params.has("error") ? "alert error" : "alert notice";
        item.textContent = message;
        alerts.appendChild(item);
    }

    const tokenInputs = document.querySelectorAll('input[name="csrf_token"]');

    if (!tokenInputs.length || isStaticPreview) {
        return;
    }

    try {
        const response = await fetch("/auth/csrf-token", {
            credentials: "same-origin"
        });

        if (!response.ok) {
            return;
        }

        const payload = await response.json();
        tokenInputs.forEach((input) => {
            input.value = payload.csrfToken || "";
        });
    } catch (error) {}
}());
