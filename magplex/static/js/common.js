class ToastType {
    static SUCCESS = 'toast-success';
    static WARNING = 'toast-warning';
    static ERROR = 'toast-error';
}

function showToast(message, toastType) {
    Toastify({
        text: message,
        duration: 3000,
        className: toastType,
        gravity: "top",
        position: "right",
        stopOnFocus: true,
    }).showToast();
}