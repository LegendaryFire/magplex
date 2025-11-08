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
                            <button id="generate-key-btn" data-confirmed="false">Generate API Key</button>
                            <button id="delete-key-btn" data-confirmed="false">Delete API Key</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        super.connectedCallback();
        await this.renderKeys();

        const generateKeyBtn = document.querySelector('#generate-key-btn');
        generateKeyBtn.addEventListener('click', async () => {
            await this.updateApiKey();
            await this.renderKeys();
        });

        const deleteKeyBtn = document.querySelector('#delete-key-btn');
        deleteKeyBtn.addEventListener('click', async () => {
            await this.deleteApiKey();
            await this.renderKeys();
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