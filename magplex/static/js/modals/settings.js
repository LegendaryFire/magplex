class SettingsModal extends Modal {
    async connectedCallback() {
        this.deviceProfile = await getDeviceProfile();
        this.modalTitle = "Settings";
        this.magplexInfo = await this.getInfo();
        this.innerHTML = `
            <div class="content-wrapper">
                <div class="content-group">
                    <h2 class="content-title">User</h2>
                    <div class="content-container">
                        <div class="button-row">
                            <button id="change-username-btn">Change Username</button>
                            <button id="change-password-btn">Change Password</button>
                        </div>
                    </div>
                </div>
            
                <div class="content-group">
                    <h2 class="content-title">Device</h2>
                    <div class="content-container">
                        <div class="button-row">
                            <button id="configure-device-btn">Configure Device</button>
                            <button id="channel-filter-btn">Channel Filter</button>
                        </div>
                    </div>
                </div>
                
                <div class="content-group">
                    <h2 class="content-title">Background Tasks</h2>
                    <div class="content-container">
                        <button id="refresh-channels-btn">Refresh Channels</button>
                        <button id="refresh-epg-btn">Refresh EPG</button>
                    </div>
                </div>
                
                <div class="content-group">
                    <h2 class="content-title">About</h2>
                    <div class="content-container">
                        <div class="about-container">
                            <div class="left-container">
                                <h1>Magplex</h1>
                                <h4>by LegendaryFire</h4>
                            </div>
                            <div class="right-container">
                                <p class="version">Version ${this.magplexInfo.version}</p>
                                <p class="build-date">${this.magplexInfo.build_date}</p>
                                <p class="build-date">Device UID: ${this?.deviceProfile.device_uid}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        super.connectedCallback();

        const configureDeviceBtn = document.querySelector('#configure-device-btn');
        configureDeviceBtn.addEventListener('click', (event) => {
            const deviceModal = document.createElement('device-modal');
            document.querySelector('body').appendChild(deviceModal);
        });

        const configureFilterBtn = document.querySelector('#channel-filter-btn');
        configureFilterBtn.addEventListener('click', (event) => {
            const channelFilterModal = document.createElement('channel-filter-modal');
            document.querySelector('body').appendChild(channelFilterModal);
        });

        const usernameBtn = document.querySelector('#change-username-btn');
        usernameBtn.addEventListener('click', (event) => {
            const usernameModal = document.createElement('username-modal');
            document.querySelector('body').appendChild(usernameModal);
        });

        const passwordBtn = document.querySelector('#change-password-btn');
        passwordBtn.addEventListener('click', (event) => {
            const passwordModal = document.createElement('password-modal');
            document.querySelector('body').appendChild(passwordModal);
        });

        const refreshChannelsBtn = document.querySelector('#refresh-channels-btn');
        refreshChannelsBtn.addEventListener('click', () => {
            this.refreshChannels();
        });

        const refreshEpgBtn = document.querySelector('#refresh-epg-btn');
        refreshEpgBtn.addEventListener('click', (event) => {
            this.refreshEpg();
        });
    }

    async getInfo() {
        try {
            const response = await fetch('/about');
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    async refreshEpg() {
        const response = await fetch(`/api/devices/${this.deviceProfile.device_uid}/channels/guides/sync`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        if (!response.ok) {
            const data = await response.json()
            const message = parseError(data);
            showToast(message, ToastType.ERROR);
        } else {
            showToast("Manual channel guide refresh has been triggered!", ToastType.SUCCESS);
        }
    }

    async refreshChannels() {
        const response = await fetch(`/api/devices/${this.deviceProfile.device_uid}/channels/sync`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        if (!response.ok) {
            const data = await response.json()
            const message = parseError(data);
            showToast(message, ToastType.ERROR);
        } else {
            showToast("Manual channel list refresh has been triggered!", ToastType.SUCCESS);
        }
    }
}

customElements.define('settings-modal', SettingsModal);