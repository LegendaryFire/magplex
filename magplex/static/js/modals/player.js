class PlayerModal extends Modal {
    constructor() {
        super();
        this.modalTitle = null;
        this.channelId = null;
        this.videoElem = null;
        this.hls = null;
    }

    async connectedCallback() {
        this.deviceProfile = await getDeviceProfile();
        this.modalTitle = this.dataset.channelName;
        this.channelId = this.dataset.channelId;

        this.innerHTML = `<video controls></video>`;
        super.connectedCallback();

        this.videoElem = document.querySelector('video');
        this.loadStream();

    }

    closeModal() {
        if (this.videoElem) {
            this.videoElem.pause();
        }

        if (this.hls) {
            this.hls.stopLoad();
            this.hls.detachMedia();
            this.hls.destroy();
            this.hls = null;
        }

        super.closeModal();
    }

    loadStream() {
        if (!Hls.isSupported()) {
            console.error("HLS is not supported in this browser");
            return;
        }

        const channelUrl = `/api/devices/${this.deviceProfile.device_uid}/channels/${this.channelId}/proxy`;
        this.hls = new Hls();
        this.hls.loadSource(channelUrl);
        this.hls.attachMedia(this.videoElem);
        this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
            this.videoElem.play().catch(err => {
                console.warn("Video play failed:", err);
            });
        });
    }
}

customElements.define('player-modal', PlayerModal)