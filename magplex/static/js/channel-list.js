class ChannelList extends HTMLElement {
    constructor() {
        super();
        this.genres = []
        this.channels = [];
    }

    async connectedCallback() {
        this.channels = await this.getChannelList();
        if (this.channels !== null) {
            this.genres = [...new Set(this.channels.map(c => c.genre_name))];
            this.appendChild(this.getSearchBarElement());
            this.appendChild(this.getChannelListElement());
            this.renderChannelList();
        } else {
            this.appendChild(this.getConfigureElement());
        }
    }

    async getChannelList() {
        try {
            const response = await fetch('/api/channels/list', {headers: {'Accept': 'application/json'}});
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    getConfigureElement() {
        const configureDeviceElem = document.createElement('div');
        configureDeviceElem.classList.add('configure-container')
        configureDeviceElem.innerHTML = `
            <h2>Unable to get channel list.</h2>
            <h3>Ensure device is configured in the about page, and try again.</h3>
        `;
        return configureDeviceElem;
    }

    getSearchBarElement() {
        const searchContainerElem = document.createElement('div');
        searchContainerElem.classList.add('search-container');
        searchContainerElem.innerHTML = `
            <input type="text" name='search' placeholder='Search...'>
            <select name='genre'>
                <option value="">All</option>
                ${this.genres.map(genre => `<option value="${genre}">${genre}</option>`).join('')}
            </select>
        `;
        const searchElem = searchContainerElem.querySelector('input');
        searchElem.addEventListener('keyup', (event) => {
            const searchVal = event.currentTarget.value;
            const genreVal = searchContainerElem.querySelector('[name=genre]').value;
            this.searchChannelList(searchVal, genreVal);
        });

        const genreElem = searchContainerElem.querySelector('select');
        genreElem.addEventListener('change', (event) => {
            const searchVal = searchContainerElem.querySelector('[name=search]').value;
            const genreVal = event.currentTarget.value;
            this.searchChannelList(searchVal, genreVal);
        });


        return searchContainerElem;
    }

    searchChannelList() {
        const searchElem = document.querySelector('.search-container [name=search]');
        const genreElem = document.querySelector('.search-container [name=genre]');
        let search = searchElem.value.trim().toLowerCase();
        search = search === '' ? null : search;
        let genre = genreElem.value.trim().toLowerCase();
        genre = genre === '' ? null : genre;
        const channelElements = document.querySelectorAll('.channel');
        for (const element of channelElements) {
            const channelName = element.dataset.channelName.toLowerCase();
            const genreName = element.dataset.genreName.toLowerCase();
            if (genre === null || genreName.includes(genre)) {
                element.hidden = false;
            } else {
                element.hidden = true;
                continue;
            }
            if (search === null || channelName.includes(search)) {
                element.hidden = false;
            } else {
                element.hidden = true;
                continue;
            }
        }
    }

    renderChannelList() {
        /** Renders the channels in the channel list container. */
        const channelListElem = this.querySelector('ul.channel-list');
        for (const channel of this.channels) {
            const channelElem = this.buildChannelElement(channel);
            channelListElem.appendChild(channelElem);
        }
    }

    getChannelListElement() {
        const channelListElem = document.createElement('ul');
        channelListElem.classList.add('channel-list');
        return channelListElem;
    }

    buildChannelElement(channel) {
        const channelElem = document.createElement('li');
        channelElem.classList.add('channel');
        channelElem.dataset['channelId'] = channel.channel_id;
        channelElem.dataset['channelName'] = channel.channel_name;
        channelElem.dataset['genreName'] = channel.genre_name;
        channelElem.dataset['streamId'] = channel.stream_id;

        channelElem.innerHTML = `
            <div class="channel-left">
                <span class="material-symbols-outlined">live_tv</span>
            </div>
            <div class="channel-details">
                <span class="channel-name">${channel.channel_name}</span>
                <span class="channel-group">${channel.genre_name}</span>
            </div>
            <div class="channel-right">
                <span class="material-symbols-outlined">hd</span>
                <span class="channel-number">${channel.channel_id}</span>
            </div>
        `

        if (typeof channelClickCallback === 'function') {
            channelElem.addEventListener('click', () => {
                channelClickCallback(channel.channel_id, channel.channel_name, channel.stream_id);
            })
        }
        return channelElem;
    }
}

customElements.define('channel-list', ChannelList);