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