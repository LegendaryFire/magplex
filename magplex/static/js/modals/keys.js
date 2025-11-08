class KeysModal extends Modal {
    constructor() {
        super();
        this.modalTitle = "Settings";
        this.passwordChanged = false;
        this.deviceProfile = null;
        this.userApiKey = null;
    }


    async connectedCallback() {
        this.deviceProfile = await getDeviceProfile();
        this.innerHTML = `
            <div class="content-wrapper">
                <div class="content-group">
                    <h2 class="content-title">API Key</h2>
                    <div class="content-container">
                        <label>
                            Device UID
                            <input id="device-uid" type="text" placeholder="No Device" value="${this.deviceProfile !== null ? `${this.deviceProfile.device_uid}` : ''}" disabled>
                        </label>
                        <label>
                            API Key
                            <input id="api-key" type="text" placeholder="No API Key" value="" disabled>
                        </label>
                        <div class="button-row">
                            <button id="generate-key-btn" data-confirmed="false">Update API Key</button>
                            <button id="delete-key-btn" data-confirmed="false">Delete API Key</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        super.connectedCallback();
        await this.renderKeys();

        const generateKeyBtn = document.querySelector('#generate-key-btn');
        let generateConfirmTimeout = null;
        generateKeyBtn.addEventListener('click', async () => {
            if (generateKeyBtn.dataset.confirmed === 'true') {
                // User confirmed within timeout
                clearTimeout(generateConfirmTimeout);
                generateConfirmTimeout = null;

                await this.updateApiKey();
                await this.renderKeys();

                generateKeyBtn.dataset.confirmed = 'false';
                generateKeyBtn.style.color = 'inherit';
                generateKeyBtn.innerText = 'Update API Key';
                return;
            }

            // First click — ask for confirmation
            generateKeyBtn.dataset.confirmed = 'true';
            generateKeyBtn.style.color = 'var(--color-warning)';
            generateKeyBtn.innerText = 'Confirm Update API Key';

            // Clear any existing timeout to prevent overlap
            clearTimeout(generateConfirmTimeout);

            generateConfirmTimeout = setTimeout(() => {
                generateKeyBtn.dataset.confirmed = 'false';
                generateKeyBtn.style.color = 'inherit';
                generateKeyBtn.innerText = 'Update API Key';
                generateConfirmTimeout = null;
            }, 3000);
        });

        const deleteKeyBtn = document.querySelector('#delete-key-btn');
        let deleteConfirmTimeout = null;
        deleteKeyBtn.addEventListener('click', async () => {
            if (deleteKeyBtn.dataset.confirmed === 'true') {
                // User confirmed within timeout
                clearTimeout(deleteConfirmTimeout);
                deleteConfirmTimeout = null;

                await this.deleteApiKey();
                await this.renderKeys();

                deleteKeyBtn.dataset.confirmed = 'false';
                deleteKeyBtn.style.color = 'inherit';
                deleteKeyBtn.innerText = 'Delete API Key';
                return;
            }

            // First click — ask for confirmation
            deleteKeyBtn.dataset.confirmed = 'true';
            deleteKeyBtn.style.color = 'var(--color-warning)';
            deleteKeyBtn.innerText = 'Confirm Delete API Key';

            // Clear any previous timeout if user spam-clicks
            clearTimeout(deleteConfirmTimeout);

            deleteConfirmTimeout = setTimeout(() => {
                deleteKeyBtn.dataset.confirmed = 'false';
                deleteKeyBtn.style.color = 'inherit';
                deleteKeyBtn.innerText = 'Delete API Key';
                deleteConfirmTimeout = null;
            }, 3000);
        });
    }

    async renderKeys() {
        this.userApiKey = await this.getApiKey();
        const deviceUidInput = this.querySelector('#device-uid');
        deviceUidInput.value = this.deviceProfile ? this.deviceProfile.device_uid : '';

        const apiKeyInput = this.querySelector('#api-key');
        apiKeyInput.value = this.userApiKey ? this.userApiKey : '';
    }

    async getApiKey() {
        try {
            const response = await fetch('/api/user/api');
            const data = await response.json();
            return data.api_key;
        } catch (error) {
            return null;
        }
    }

    async updateApiKey() {
        try {
            const response = await fetch('/api/user/api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                showToast("API key has been updated successfully", ToastType.SUCCESS);
            }
        } catch (error) {
            return null;
        }
    }

    async deleteApiKey() {
        try {
            const response = await fetch('/api/user/api', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                showToast("API key has been deleted successfully", ToastType.WARNING);
            }
        } catch (error) {
            return null;
        }
    }

    closeModal() {
        this.remove();
    }
}

customElements.define('keys-modal', KeysModal)