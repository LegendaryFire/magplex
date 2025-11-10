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
                                <small>Optional: Enter the 64-character hex Device ID 1. Required by some providers.</small>
                            </label>
                            <label>
                                Device ID 2
                                <input type="text" name="device_id2" placeholder="0000000000000000000000000000000000000000000000000000000000000000" value="${deviceProfile?.device_id2 ?? ''}">
                                <small>Optional: Enter the 64-character hex Device ID 2. Required by some providers.</small>
                            </label>
                            <label>
                                Signature
                                <input type="text" name="signature" placeholder="0000000000000000000000000000000000000000000000000000000000000000" value="${deviceProfile?.signature ?? ''}">
                                <small>Optional: Enter the 64-character hex signature. Required by some providers.</small>
                            </label>
                            <label>
                                Timezone
                                <input type="text" name="timezone" placeholder="America/Vancouver" value="${deviceProfile?.timezone ?? ''}" required>
                                <small>Enter the timezone you want the portal to use. Primarily used for channel guides.</small>
                            </label>
                            <label>
                                Portal
                                <input type="text" name="portal" placeholder="example.portal.tv" value="${deviceProfile?.portal ?? ''}" required>
                                <small>Enter the portal domain, without scheme. Example: provider.portal.tv</small>
                            </label>
                            <button type="submit">Save</button>
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
            showToast("Device settings have been saved successfully!", ToastType.SUCCESS);
        }
    }
}

customElements.define('device-modal', DeviceModal);