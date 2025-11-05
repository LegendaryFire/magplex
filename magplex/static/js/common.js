class ToastType {
    static SUCCESS = 'toast-success';
    static WARNING = 'toast-warning';
    static ERROR = 'toast-error';
}

function showToast(message, toastType) {
    Toastify({
        text: message,
        duration: 2500,
        className: toastType,
        gravity: "top",
        position: "center",
    }).showToast();
}

function serializeForm(form) {
    const formData = new FormData(form);
    const obj = {};
    for (const [key, value] of formData.entries()) {
        obj[key] = value;
    }
    return obj;
}

function parseError(response) {
    const errorMessage = response?.error?.message;
    return errorMessage ? errorMessage : "Unknown error occurred.";
}

async function getDeviceProfile() {
    try {
        const response = await fetch('/api/user/device');
        return await response.json();
    } catch (error) {
        return null;
    }
}