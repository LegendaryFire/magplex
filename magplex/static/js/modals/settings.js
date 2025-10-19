class SettingsModal extends Modal {
    async connectedCallback() {
        const aboutInfo = await this.getInfo();

        this.modalTitle = "Settings";
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
                        </div>
                    </div>
                </div>
                
                <div class="content-group">
                    <h2 class="content-title">Background Tasks</h2>
                    <div class="content-container">
                        <button id="refresh-epg-btn">Refresh EPG</button>
                    </div>
                </div>
                <div class="content-group">
                    <div class="about-container">
                        <div class="left-container">
                            <h1>Magplex</h1>
                            <h4>by LegendaryFire</h4>
                        </div>
                        <div class="right-container">
                            <p class="version">Version ${aboutInfo.version}</p>
                            <p class="build-date">${aboutInfo.build_date}</p>
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
        try {
            await fetch('/api/device/channels/guides', {
                method: 'POST'
            });
        } catch (error) {
            return null;
        }
    }
}

customElements.define('settings-modal', SettingsModal);