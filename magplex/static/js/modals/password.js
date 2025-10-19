class PasswordModal extends Modal {
    constructor() {
        super();
        this.modalTitle = "Settings";
        this.passwordChanged = false;
    }

    async connectedCallback() {
        this.innerHTML = `
            <div class="content-wrapper">
                <div class="content-group">
                    <h2 class="content-title">Change Password</h2>
                    <div class="content-container">
                        <form id="password-form">
                            <label>
                                Password
                                <input type="password" name="current_password" placeholder="Current Password" required>
                            </label>
                            <label>
                                New Password
                                <input type="password" name="new_password" placeholder="New Password" required>
                            </label>
                            <label>
                                New Password Again
                                <input type="password" name="new_password_repeated" placeholder="New Password Again" required>
                            </label>
                            <button type="submit">Save</button>
                        </form>
                    </div>
                </div>
            </div>
        `;
        super.connectedCallback();

        const passwordForm = document.querySelector('#password-form');
        passwordForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const formData = serializeForm(passwordForm);
            if (await this.savePassword(formData)) {
                this.closeModal();
            }
        });
    }

    async savePassword(formData) {
        const response = await fetch('/api/user/password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const data = await response.json()
            const message = parseError(data);
            showToast(message, ToastType.ERROR);
            return false;
        } else {
            showToast("Password has been updated successfully!", ToastType.SUCCESS);
            this.passwordChanged = true;
            return true;
        }
    }

    closeModal() {
        if (this.passwordChanged) {
            window.location.href = '/';
        }
    }
}

customElements.define('password-modal', PasswordModal)