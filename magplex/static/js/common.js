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


function showThrobber(messageTitle='Loading', messageDescription='Please wait...') {
    // Force one throbber at a time.
    let throbber = document.querySelector('throbber-overlay');
    if (document.querySelector('throbber-overlay')) {
        return;
    }

    throbber = document.createElement('throbber-overlay');
    throbber.setAttribute('message-title', messageTitle);
    throbber.setAttribute('message-description', messageDescription);
    document.querySelector('body').appendChild(throbber);
}


function hideThrobber() {
    const throbber = document.querySelector('throbber-overlay');
    if (throbber) {
        throbber.remove();
    }
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

function debounceFn(fn, delay = 300) {
  let timer, controller;
  return (...args) => {
    clearTimeout(timer);
    if (controller) controller.abort();
    controller = new AbortController();
    timer = setTimeout(() => fn(...args, controller.signal), delay);
  };
}