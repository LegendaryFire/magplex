class SettingsModal extends Modal {
    async connectedCallback() {
        this.modalTitle = "Settings";
        this.deviceProfile = await getDeviceProfile();
        this.magplexInfo = await this.getMagplexInfo();
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
                            <button id="configure-device-btn">Device Configuration</button>
                        </div>
                        <div class="button-row">
                            <button id="channel-filter-btn" ${this.deviceProfile === null ? 'disabled' : ''}>Channel Filter</button>
                            <button id="api-keys-btn" ${this.deviceProfile === null ? 'disabled' : ''}>API Key</button>
                        </div>
                    </div>
                </div>
                
                <div class="content-group">
                    <h2 class="content-title">Background Tasks</h2>
                    <div class="content-container">
                        <button id="refresh-channels-btn" ${this.deviceProfile === null ? 'disabled' : ''}>Refresh Channels</button>
                        <div id="refresh-channels-runtime" class="task-timestamp">Last Runtime: Never</div>
                        <button id="refresh-epg-btn" ${this.deviceProfile === null ? 'disabled' : ''}>Refresh EPG</button>
                        <div id="refresh-epg-runtime"  class="task-timestamp">Last Runtime: Never</div>
                    </div>
                </div>
                
                <div class="content-group">
                    <h2 class="content-title">About</h2>
                    <div class="content-container">
                        <div class="about-container">
                            <div class="left-container">
                                <h2>Magplex</h2>
                                <h4>by LegendaryFire</h4>
                            </div>
                            <div class="right-container">
                                <p class="version">Version ${this.magplexInfo.version}</p>
                                <p class="build-date">${this.magplexInfo.build_date}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        super.connectedCallback();

        await this.renderTaskRuntimes();

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

        const apiKeysBtn = document.querySelector('#api-keys-btn');
        apiKeysBtn.addEventListener('click', (event) => {
            const apiKeysModal = document.createElement('keys-modal');
            document.querySelector('body').appendChild(apiKeysModal);
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
            this.triggerChannelSync();
        });

        const refreshEpgBtn = document.querySelector('#refresh-epg-btn');
        refreshEpgBtn.addEventListener('click', (event) => {
            this.triggerGuideSync();
        });
    }

    async getMagplexInfo() {
        try {
            const response = await fetch('/about');
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    async getTaskRuntimes() {
        try {
            const response = await fetch(`/api/devices/${this.deviceProfile.device_uid}/tasks`);
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    async renderTaskRuntimes() {
        const channelRuntimeLabel = this.querySelector('#refresh-channels-runtime');
        const guideRuntimeLabel = this.querySelector('#refresh-epg-runtime');
        channelRuntimeLabel.innerText = 'Last Run: Never';
        guideRuntimeLabel.innerText = 'Last Run: Never';
        if (this.deviceProfile === null) {
            return;
        }

        const deviceTaskRuntimes = await this.getTaskRuntimes();
        const channelsTask = deviceTaskRuntimes.find((task) => task.task_name === 'save_channels');
        const guidesTask = deviceTaskRuntimes.find((task) => task.task_name === 'save_channel_guides');
        const dateFormatter = new Intl.DateTimeFormat("en-US", {
            month: "short", day: "numeric", year: "numeric",
            hour: "numeric", minute: "2-digit", hour12: true,
            timeZoneName: "short"
        });

        if (channelsTask) {
            const runDate = new Date(channelsTask.creation_timestamp);
            channelRuntimeLabel.innerText = `Last Run: ${dateFormatter.format(runDate)}`;
        }

        if (guidesTask) {
            const runDate = new Date(guidesTask.creation_timestamp);
            guideRuntimeLabel.innerText = `Last Run: ${dateFormatter.format(runDate)}`;
        }
    }

    async triggerGuideSync() {
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

    async triggerChannelSync() {
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