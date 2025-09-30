class MediaPlayer extends HTMLElement {
    connectedCallback() {
        this.hidePlayer();
        this.innerHTML = `
            <button class="close-btn">Close</button>
            <video controls>
            </video>
        `;
        const closeBtn = this.querySelector('.close-btn');
        closeBtn.addEventListener('click', () => this.hidePlayer());
    }

    showPlayer() {
        this.hidden = false;
    }

    hidePlayer() {
        this.hidden = true;
    }

    playStream(url) {
        const videoElem = document.querySelector('video');
        const hls = new Hls();
        hls.loadSource(url);
        hls.attachMedia(videoElem);
        hls.on(Hls.Events.MANIFEST_PARSED, function() {
            video.play();
        });
    }

}

customElements.define('media-player', MediaPlayer)