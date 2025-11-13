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
                        <button id="refresh-epg-btn" ${this.deviceProfile === null ? 'disabled' : ''}>Refresh EPG</button>
                        <h4 class="table-title">Completed Tasks</h4>
                        <div class="table-container completed-tasks">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Task</th>
                                        <th>Completed</th>
                                    </tr>
                                </thead>
                                <tbody></tbody>
                            </table>
                        </div>
                        <h4 class="table-title">Incomplete Tasks</h4>
                        <div class="table-container incomplete-tasks">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Task</th>
                                        <th>Started</th>
                                    </tr>
                                </thead>
                                <tbody></tbody>
                            </table>
                        </div>
                        <div class="button-row">
                            <button id="refresh-logs-btn" ${this.deviceProfile === null ? 'disabled' : ''}>Refresh Logs</button>
                        </div>
                        <div class="button-row">
                            <button id="clear-logs-btn" ${this.deviceProfile === null ? 'disabled' : ''}>Clear All Logs</button>
                            <button id="clear-incomplete-btn" ${this.deviceProfile === null ? 'disabled' : ''}>Clear Incomplete Logs</button>
                        </div>
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
        await this.renderTaskTables();

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
        refreshChannelsBtn.addEventListener('click', async () => {
            await this.triggerChannelSync();
        });

        const refreshEpgBtn = document.querySelector('#refresh-epg-btn');
        refreshEpgBtn.addEventListener('click', async () => {
            await this.triggerGuideSync();
        });

        const refreshLogsBtn = document.querySelector('#refresh-logs-btn');
        refreshLogsBtn.addEventListener('click', async (t) => {
            await this.renderTaskTables();
            showToast('Task logs have been refreshed successfully', ToastType.SUCCESS);
        });

        const clearLogsBtn = document.querySelector('#clear-logs-btn');
        clearLogsBtn.addEventListener('click', async () => {
            await this.clearTaskLogs();
            await this.renderTaskTables();
        });

        const clearIncompleteBtn = document.querySelector('#clear-incomplete-btn');
        clearIncompleteBtn.addEventListener('click', async () => {
            await this.clearTaskLogs(false);
            await this.renderTaskTables();
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

    async getTaskLogs(isCompleted) {
        try {
            const taskLogUrl = new URL(`/api/devices/${this.deviceProfile.device_uid}/tasks`, window.location.origin);
            taskLogUrl.searchParams.set('is_completed', isCompleted);
            const response = await fetch(taskLogUrl);
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    async clearTaskLogs(isCompleted=null) {
        try {
            const taskLogUrl = new URL(`/api/devices/${this.deviceProfile.device_uid}/tasks`, window.location.origin);
            await fetch(taskLogUrl, {
                method: 'DELETE',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({'is_completed': isCompleted})
            });
            if (isCompleted === null) {
                showToast("All task logs have been deleted successfully", ToastType.SUCCESS);
            } else if (isCompleted === true) {
                showToast("Completed task logs have been deleted successfully", ToastType.SUCCESS);
            } else {
                showToast("Incomplete task logs have been deleted successfully", ToastType.SUCCESS);
            }
        } catch (error) {
            return [];
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
            showToast("Manual channel guide refresh has been triggered", ToastType.SUCCESS);
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
            showToast("Manual channel list refresh has been triggered", ToastType.SUCCESS);
        }
    }

    async renderTaskTables() {
        const completedTableBody = this.querySelector('div.completed-tasks table tbody');
        const incompleteTableBody = this.querySelector('div.incomplete-tasks table tbody');

        const noTasksTemplate = document.createElement('template');
        noTasksTemplate.innerHTML = `
            <tr>
                <td class="center" colspan="2">No Tasks</td>
            </tr>
        `.trim();


        if (this.deviceProfile === null) {
            completedTableBody.innerHTML = '';
            incompleteTableBody.innerHTML = '';
            completedTableBody.appendChild(noTasksTemplate.content.cloneNode(true));
            incompleteTableBody.appendChild(noTasksTemplate.content.cloneNode(true));
            return;
        }

        const dateFormatter = new Intl.DateTimeFormat("en-US", {
            month: "short", day: "numeric", year: "numeric",
            hour: "numeric", minute: "2-digit", hour12: true,
            timeZoneName: "short"
        });

        const taskMap = {
            'save_channels': "Save Channels",
            'save_channel_guides': "Save Guides"
        }

        const completedTaskRuntimes = await this.getTaskLogs(true);
        const incompleteTaskRuntimes = await this.getTaskLogs(false);
        completedTableBody.innerHTML = '';
        incompleteTableBody.innerHTML = '';
        if (completedTaskRuntimes.length === 0) {
            completedTableBody.appendChild(noTasksTemplate.content.cloneNode(true));
        } else {
            completedTaskRuntimes.forEach((task) => {
                const template = document.createElement('template');
                const taskTimestamp = new Date(task.completed_timestamp);
                const friendlyName = taskMap[task.task_name];
                template.innerHTML = `
                    <tr>
                        <td>${friendlyName ? friendlyName : task.task_name}</td>
                        <td>${dateFormatter.format(taskTimestamp)}</td>
                    </tr>
                `.trim();
                completedTableBody.appendChild(template.content.cloneNode(true));
            });
        }

        if (incompleteTaskRuntimes.length === 0) {
            incompleteTableBody.appendChild(noTasksTemplate.content.cloneNode(true));
        } else {
            incompleteTaskRuntimes.forEach((task) => {
                const template = document.createElement('template');
                const taskTimestamp = new Date(task.started_timestamp);
                const friendlyName = taskMap[task.task_name];
                template.innerHTML = `
                    <tr>
                        <td>${friendlyName ? friendlyName : task.task_name}</td>
                        <td>${dateFormatter.format(taskTimestamp)}</td>
                    </tr>
                `.trim();
                incompleteTableBody.appendChild(template.content.cloneNode(true));
            });
        }
    }
}

customElements.define('settings-modal', SettingsModal);