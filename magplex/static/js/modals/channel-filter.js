class ChannelFilterModal extends Modal {
    constructor() {
        super();
        this.refreshOnClose = false;
    }

    async connectedCallback() {
        this.deviceProfile = await getDeviceProfile();
        this.modalTitle = "Settings";
        this.innerHTML = `
            <div class="content-wrapper">
                <div class="content-group">
                    <h2 class="content-title">Channel Filter</h2>
                    <div class="content-container">
                    <div class="button-row">
                        <button id="enable-all-btn">Enable All</button>
                        <button id="disable-all-btn">Disable All</button>
                    </div>
                        <form id="device-form">
                            <channel-list list-mode="filter"></channel-list>
                        </form>
                    </div>
                </div>
            </div>
        `;
        super.connectedCallback();

        const enableAllBtn = this.querySelector('#enable-all-btn');
        enableAllBtn.addEventListener('click', async () => {
            await this.toggleAllChannels(true);
            this.connectedCallback();
        });

        const disableAllBtn = this.querySelector('#disable-all-btn');
        disableAllBtn.addEventListener('click', async () => {
            await this.toggleAllChannels(false);
            this.connectedCallback();
        });

        this.querySelector('channel-list[list-mode=filter]').channelToggleCallback = await this.toggleChannel.bind(this);
    }

    async toggleAllChannels(channelsEnabled) {
        const response = await fetch(`/api/devices/${this.deviceProfile.device_uid}/channels`, {
            method: 'POST',
            body: JSON.stringify({'channel_enabled': channelsEnabled}),
            headers: {'Content-Type': 'application/json'}
        });

        if (!response.ok) {
            const data = await response.json()
            const message = parseError(data);
            showToast(message, ToastType.ERROR);
            return;
        }

        this.refreshOnClose = true;
        if (channelsEnabled === true) {
            showToast(`All channels enabled successfully.`, ToastType.SUCCESS);
        } else {
            showToast(`All channels disabled successfully.`, ToastType.WARNING);
        }
    }

    async toggleChannel(channelId, channelEnabled) {
        const response = await fetch(`/api/devices/${this.deviceProfile.device_uid}/channels/${channelId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({'channel_id': channelId, 'channel_enabled': channelEnabled})
        });

        if (!response.ok) {
            const data = await response.json()
            const message = parseError(data);
            showToast(message, ToastType.ERROR);
            return;
        }

        this.refreshOnClose = true;
        if (channelEnabled === true) {
            showToast(`Channel enabled successfully.`, ToastType.SUCCESS);
        } else {
            showToast(`Channel disabled successfully.`, ToastType.WARNING);
        }
    }

    async closeModal () {
        if (this.refreshOnClose) {
            await document.querySelector('channel-list').updateChannelList();
        }
        this.remove();
    }
}

customElements.define('channel-filter-modal', ChannelFilterModal);