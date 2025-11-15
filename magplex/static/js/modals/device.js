class DeviceModal extends Modal {
    async connectedCallback() {
        const deviceProfile = await getDeviceProfile();
        this.modalTitle = "Settings";
        this.innerHTML = `
            <div class="content-wrapper">
                <div class="content-group">
                    <h2 class="content-title">Device</h2>
                    <div class="content-container">
                        <form id="device-form">
                            <label>
                                MAC Address
                                <input type="text" name="mac_address" placeholder="00-00-00-00-00-00" value="${deviceProfile?.mac_address ?? ''}" required>
                                <small>Enter the MAC address, found on the bottom of the device.</small>
                            </label>
                            <label>
                                Device ID 1
                                <input type="text" name="device_id1" placeholder="0000000000000000000000000000000000000000000000000000000000000000" value="${deviceProfile?.device_id1 ?? ''}">
                                <small>Enter the 64-character hex Device ID 1. Required by some providers.</small>
                            </label>
                            <label>
                                Device ID 2
                                <input type="text" name="device_id2" placeholder="0000000000000000000000000000000000000000000000000000000000000000" value="${deviceProfile?.device_id2 ?? ''}">
                                <small>Enter the 64-character hex Device ID 2. Required by some providers.</small>
                            </label>
                            <label>
                                Timezone
                                <input type="text" name="timezone" placeholder="America/Vancouver" value="${deviceProfile?.timezone ?? ''}" required>
                                <small>Enter the timezone you want the portal to use. Primarily used for channel guides.</small>
                            </label>
                            <label>
                                Portal
                                <input type="text" name="portal" placeholder="example.portal.tv" value="${deviceProfile?.portal ?? ''}" required ${deviceProfile?.portal ? 'disabled' : ''}>
                                <small>Enter the portal domain, <b>with</b> scheme. Example: http://provider.portal.tv</small>
                            </label>
                            <button type="submit">Save</button>
                            <button id="delete-btn">Delete Device</button>
                        </form>
                    </div>
                </div>
            </div>
        `;
        super.connectedCallback();

        const deviceForm = document.querySelector('#device-form');
        deviceForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const deviceProfile = serializeForm(deviceForm);
            this.saveDevice(deviceProfile);
        });

        const deleteDeviceBtn = document.querySelector('#delete-btn');
        deleteDeviceBtn.addEventListener('click', (event) => {
            event.preventDefault();
            this.deleteDevice(deviceProfile);
        });
    }

    async saveDevice(deviceProfile) {
        const response = await fetch('/api/user/device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(deviceProfile)
        });

        if (!response.ok) {
            const data = await response.json()
            const message = parseError(data);
            showToast(message, ToastType.ERROR);
        } else {
            showThrobber("Saving Device", "Please wait...")
            await document.querySelector('channel-list').connectedCallback();
            await document.querySelector('settings-modal').connectedCallback();
            hideThrobber();
            showToast("Device settings have been saved successfully!", ToastType.SUCCESS);
            this.connectedCallback();
        }
    }

    async deleteDevice() {
        const response = await fetch('/api/user/device', {
            method: 'DELETE',
        });

        if (!response.ok) {
            const data = await response.json()
            const message = parseError(data);
            showToast(message, ToastType.ERROR);
        } else {
            showThrobber("Deleting Device", "Please wait...")
            await document.querySelector('channel-list').connectedCallback();
            await document.querySelector('settings-modal').connectedCallback();
            hideThrobber();
            showToast("Device has been deleted successfully!", ToastType.WARNING);
            this.connectedCallback();
        }
    }
}

customElements.define('device-modal', DeviceModal);