class DeviceModal extends Modal {
    async connectedCallback() {
        const device = await this.getDevice();
        this.modalTitle = "Settings";
        this.innerHTML = `
            <div class="content-wrapper">
                <div class="content-group">
                    <h2 class="content-title">Device</h2>
                    <div class="content-container">
                        <form id="device-form">
                            <label>
                                MAC Address
                                <input type="text" name="mac_address" placeholder="00-00-00-00-00-00" value="${device?.mac_address ?? ''}" required>
                            </label>
                            <label>
                                Device ID 1
                                <input type="text" name="device_id1" placeholder="0000000000000000000000000000000000000000000000000000000000000000" value="${device?.device_id1 ?? ''}">
                            </label>
                            <label>
                                Device ID 2
                                <input type="text" name="device_id2" placeholder="0000000000000000000000000000000000000000000000000000000000000000" value="${device?.device_id2 ?? ''}">
                            </label>
                            <label>
                                Signature
                                <input type="text" name="signature" placeholder="0000000000000000000000000000000000000000000000000000000000000000" value="${device?.signature ?? ''}">
                            </label>
                            <label>
                                Language
                                <input type="text" name="language" placeholder="en" value="${device?.language ?? ''}" required>
                            </label>
                            <label>
                                Timezone
                                <input type="text" name="timezone" placeholder="America/Vancouver" value="${device?.timezone ?? ''}" required>
                            </label>
                            <label>
                                Portal
                                <input type="text" name="portal" placeholder="example.portal.tv" value="${device?.portal ?? ''}" required>
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
            const device = serializeForm(deviceForm);
            this.saveDevice(device);
        });
    }

    async getDevice() {
        try {
            const response = await fetch('/api/user/device');
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    async saveDevice(device) {
        const response = await fetch('/api/user/device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(device)
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