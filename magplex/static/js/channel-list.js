class ChannelList extends HTMLElement {
    constructor() {
        super();
        this.channels = [];
        this.searchMap = {};
    }

    async connectedCallback() {
        this.appendChild(this.getSearchBarElement());
        this.appendChild(this.getChannelListElement());
        this.channels = await this.getChannelList();
        this.renderChannelList();
        this.searchMap = this.getSearchMap();
    }

    getSearchMap() {
        const channelElems = this.querySelectorAll('ul li.channel');
        const searchMap = {};
        for (const channelElem of channelElems) {
            const channelId = channelElem.dataset.channelId.toLowerCase();
            const channelName = channelElem.dataset.channelName.toLowerCase();
            const genreName = channelElem.dataset.genreName.toLowerCase();
            const searchKey = `${channelId}${channelName}${genreName}`.toLowerCase();
            searchMap[searchKey] = channelElem;
        }
        return searchMap;
    }

    async getChannelList() {
        try {
            const response = await fetch('/api/channels/list', {headers: {'Accept': 'application/json'}});
            return await response.json();
        } catch (error) {
            console.log(error);
            return [];
        }
    }

    getSearchBarElement() {
        const searchContainerElem = document.createElement('div');
        searchContainerElem.classList.add('search-container');
        searchContainerElem.innerHTML = `
            <input type="text" name='search' placeholder='Search...'>
        `;
        const inputElem = searchContainerElem.querySelector('input');
        inputElem.addEventListener('keyup', (event) => {
            this.searchChannelList(event.currentTarget.value)
        });
        return searchContainerElem;
    }

    searchChannelList(search) {
        search = search.trim().toLowerCase();
        for (const [searchKey, channelElem] of Object.entries(this.searchMap)) {
            channelElem.hidden = !searchKey.includes(search);
        }
    }

    renderChannelList() {
        /**Renders the channels in the channel list container.*/
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