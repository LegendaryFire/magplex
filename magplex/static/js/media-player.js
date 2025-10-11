class MediaPlayer extends Modal {
    constructor() {
        super();
        this.modalTitle = null;
        this.streamId = null;
        this.videoElem = null;
        this.hls = null;
    }

    connectedCallback() {
        this.modalTitle = this.dataset.channelName;
        this.streamId = this.dataset.streamId;

        this.innerHTML = `<video controls></video>`;
        super.connectedCallback();

        this.videoElem = document.querySelector('video');
        this.loadStream();

    }

    onClose() {
        if (this.videoElem) {
            this.videoElem.pause();
        }

        if (this.hls) {
            this.hls.stopLoad();
            this.hls.detachMedia();
            this.hls.destroy();
            this.hls = null;
        }

        super.onClose();
    }

    loadStream() {
        if (!Hls.isSupported()) {
            console.error("HLS is not supported in this browser");
            return;
        }

        const channelUrl = `/proxy/channels/${this.streamId}`;
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

customElements.define('media-player', MediaPlayer)