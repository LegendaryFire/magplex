class ChannelFilterModal extends Modal {
    constructor() {
        super();
        this.refreshChannelList = false;
    }

    async connectedCallback() {
        this.modalTitle = "Settings";
        this.innerHTML = `
            <div class="content-wrapper">
                <div class="content-group">
                    <h2 class="content-title">Channel Filter</h2>
                    <div class="content-container">
                        <form id="device-form">
                            <channel-list edit-mode></channel-list>
                        </form>
                    </div>
                </div>
            </div>
        `;
        super.connectedCallback();

        this.querySelector('channel-list').channelToggleCallback = this.toggleChannel.bind(this);
    }

    async toggleChannel(channelId, channelName, enable) {
        if (enable) {
            const response = await fetch(`/api/device/channels/${channelId}/enable`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });

            if (!response.ok) {
                const data = await response.json()
                const message = parseError(data);
                showToast(message, ToastType.ERROR);
                return;
            }
        } else {
            const response = await fetch(`/api/device/channels/${channelId}/disable`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });

            if (!response.ok) {
                const data = await response.json()
                const message = parseError(data);
                showToast(message, ToastType.ERROR);
                return
            }
        }
        this.refreshChannelList = true;
        showToast(`Channel ${channelId} ${enable ? 'enabled' : 'disabled'} successfully.`, ToastType.SUCCESS);
    }

    closeModal() {
        if (this.refreshChannelList) {
            document.querySelector('channel-list').connectedCallback();
        }
        this.remove();
    }
}

customElements.define('channel-filter-modal', ChannelFilterModal);