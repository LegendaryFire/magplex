class AboutModal extends Modal {
    async connectedCallback() {
        const aboutInfo = await this.getInfo();
        const device = await this.getDevice();
        const user = await this.getUser();

        this.modalTitle = "About";
        this.innerHTML = `
            <div class="content-wrapper">
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
                <div class="content-group">
                    <h2 class="content-title">Device</h2>
                    <div class="content-container">
                        <form id="device-form">
                            <label>
                                MAC Address
                                <input type="text" name="mac_address" placeholder="D4-3A-E9-A3-EF-C7" value="${device?.mac_address ?? ''}" required>
                            </label>
                            <label>
                                Device ID 1
                                <input type="text" name="device_id1" placeholder="9F238DDD45B637EED88C83C220E8CABFD82E89E2135961F4383C590C4AA7EE98" value="${device?.device_id1 ?? ''}">
                            </label>
                            <label>
                                Device ID 2
                                <input type="text" name="device_id2" placeholder="BF63FB6C5C52EAD90CD0B6B257EDEB06B77FFA3EDA96DAEE2385C48091E171A0" value="${device?.device_id2 ?? ''}">
                            </label>
                            <label>
                                Signature
                                <input type="text" name="signature" placeholder="0B59594118C1F594175717F92D25218AD9674D990829175674F08D7FE2BD9DE0" value="${device?.signature ?? ''}">
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
                <div class="content-group">
                    <h2 class="content-title">Credentials</h2>
                    <div class="content-container">
                        <form id="user-form">
                            <label>
                                Username
                                <input type="text" name="username" placeholder="${user?.username ?? ''}" required>
                            </label>
                            <label>
                                Current Password
                                <input type="password" name="current_password" placeholder="Current Password" required>
                            </label>
                            <label>
                                New Password
                                <input type="password" name="new_password" placeholder="New Password">
                            </label>
                            <label>
                                New Password Confirmed
                                <input type="password" name="new_password_confirmed" placeholder="New Password Confirmed">
                            </label>
                            <button type="submit">Save</button>
                        </form>
                    </div>
                </div>
                <div class="content-group">
                    <h2 class="content-title">Background Tasks</h2>
                    <div class="content-container">
                        <button id="refresh-epg-btn">Refresh EPG</button>
                    </div>
                </div>
            </div>
        `;
        super.connectedCallback();

        const deviceForm = document.querySelector('#device-form');
        deviceForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const device = this.serializeForm(deviceForm);
            this.saveDevice(device);
        });

        const userForm = document.querySelector('#user-form');
        userForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const user = this.serializeForm(userForm);
            this.saveUser(user);
        });

        const refreshEpgBtn = document.querySelector('#refresh-epg-btn');
        refreshEpgBtn.addEventListener('click', (event) => {
            this.refreshEpg();
        });
    }

    serializeForm(form) {
        const formData = new FormData(form);
        const obj = {};
        for (const [key, value] of formData.entries()) {
            obj[key] = value;
        }
        return obj;
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
            await fetch('/refresh-epg', {
                method: 'POST'
            });
        } catch (error) {
            return null;
        }
    }

    async getDevice() {
        try {
            const response = await fetch('/device');
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    async saveDevice(device) {
        const response = await fetch('/device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(device)
        });

        if (!response.ok) {
            showToast(await response.text(), ToastType.ERROR);
        } else {
            showToast("Device settings have been saved successfully!", ToastType.SUCCESS);
        }
    }

    async getUser() {
        try {
            const response = await fetch('/user');
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    async saveUser(user) {
        const response = await fetch('/user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(user)
        });

        if (!response.ok) {
            showToast(await response.text(), ToastType.ERROR);
        } else {
            showToast("User credentials have been saved successfully!", ToastType.SUCCESS);
        }
    }
}

customElements.define('about-modal', AboutModal);