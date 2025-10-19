class UsernameModal extends Modal {
    constructor() {
        super();
        this.modalTitle = "Settings";
    }

    async connectedCallback() {
        const userAccount = await this.getUser();
        this.innerHTML = `
            <div class="content-wrapper">
                <div class="content-group">
                    <h2 class="content-title">Change Username</h2>
                    <div class="content-container">
                        <form id="username-form">
                            <label>
                                Current Username
                                <input type="text" name="current_username" placeholder="${userAccount?.username ?? ''}" required>
                            </label>
                            <label>
                                New Username
                                <input type="text" name="new_username" placeholder="New Username" required>
                            </label>
                            <label>
                                Password
                                <input type="password" name="password" placeholder="Current Password" required>
                            </label>
                            <button type="submit">Save</button>
                        </form>
                    </div>
                </div>
            </div>
        `;
        super.connectedCallback();

        const usernameForm = document.querySelector('#username-form');
        usernameForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const formData = serializeForm(usernameForm);
            if (await this.saveUsername(formData)) {
                this.closeModal();
            }
        });
    }

    async getUser() {
        try {
            const response = await fetch('/api/user');
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    async saveUsername(formData) {
        const response = await fetch('/api/user/username', {
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
            showToast("Username has been updated successfully!", ToastType.SUCCESS);
            return true;
        }
    }
}

customElements.define('username-modal', UsernameModal)