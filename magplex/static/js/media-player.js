class MediaPlayer extends HTMLElement {
    constructor() {
        super();
        this.channelId = null;
        this.channelName = null;
        this.hls = new Hls();
    }

    connectedCallback() {
        this.channelId = this.dataset.channelId;
        this.channelName = this.dataset.channelName;
        this.innerHTML = `
            <div class="modal-container">
                <div class="header">
                    <h3 class="channel-name">${this.channelName}</h3>
                    <span class="close-btn material-symbols-outlined">close</button>        
                </div>
                <video controls></video>
            </div>
        `;
        const closeBtn = this.querySelector('.close-btn');
        closeBtn.addEventListener('click', () => this.closePlayer());
        this.loadStream();
    }

    closePlayer() {
        const videoElem = document.querySelector('video');
        videoElem.pause();
        this.hls.stopLoad();
        this.hls.detachMedia();
        this.hls.destroy();
        this.remove();
    }

    loadStream() {
        const channelUrl = `/proxy/channels/${this.channelId}`;
        const videoElem = document.querySelector('video');
        this.hls.loadSource(channelUrl);
        this.hls.attachMedia(videoElem);
        this.hls.on(Hls.Events.MANIFEST_PARSED, function() {
            videoElem.play();
        });
    }

}

customElements.define('media-player', MediaPlayer)