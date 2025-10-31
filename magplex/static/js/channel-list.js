class ChannelList extends HTMLElement {
    constructor() {
        super();
        this.genres = []
        this.channels = [];
        this.editMode = false;
    }

    async connectedCallback() {
        this.editMode = this.hasAttribute('edit-mode');
        this.innerHTML = `
            <div class="message-container">
                <h2>Loading channel list.</h2>
                <h3>Please wait...</h3>
            </div>
        `
        this.channels = await this.getChannelList();
        this.genres = await this.getGenreList();
        this.innerHTML = ``;
        if (this.channels !== null) {
            this.appendChild(this.getSearchBarElement());
            this.appendChild(this.getChannelListElement());
            this.renderChannelList();
        } else {
            this.appendChild(this.getConfigureElement());
        }
    }

    async getGenreList() {
        try {
            const response = await fetch(`/api/device/genres${!this.editMode ? '?state=enabled' : ''}`, {
                headers: {
                    'Accept': 'application/json'
                }
            });
            const genres = await response.json();
            return genres.sort((a, b) => a.genre_number - b.genre_number);
        } catch (error) {
            return null;
        }
    }

    async getChannelList() {
        try {
            const response = await fetch(`/api/device/channels${!this.editMode ? '?state=enabled' : ''}`, {
                headers: {
                    'Accept': 'application/json'
                }
            });
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    getConfigureElement() {
        const configureDeviceElem = document.createElement('div');
        configureDeviceElem.classList.add('message-container')
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
                ${this.editMode ? '<option value="selected">Selected Channels</option>' : ''}
                ${this.genres.map(genre => `<option value="${genre.genre_id}">${genre.genre_name}</option>`).join('')}
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
        const searchElem = this.querySelector('.search-container [name=search]');
        const genreElem = this.querySelector('.search-container [name=genre]');
        let search = searchElem.value.trim().toLowerCase();
        search = search === '' ? null : search;
        let genreId = genreElem.value.trim().toLowerCase();
        genreId = genreId === '' ? null : genreId;
        const searchOnlySelected = this.editMode && genreId === 'selected';
        const channelElements = this.querySelectorAll('.channel');
        for (const element of channelElements) {
            const channelName = element.dataset.channelName.toLowerCase();
            if (searchOnlySelected) {
                if (element.hasAttribute('selected')) {
                    element.hidden = false;
                } else {
                    element.hidden = true;
                    continue;
                }
            } else {
                const channelGenreId = element.dataset.genreId;
                if (genreId === null || channelGenreId === genreId) {
                    element.hidden = false;
                } else {
                    element.hidden = true;
                    continue;
                }
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
        channelListElem.toggleAttribute('edit-mode', this.editMode);
        return channelListElem;
    }

    buildChannelElement(channel) {
        const channelElem = document.createElement('li');
        channelElem.classList.add('channel');
        channelElem.dataset['channelId'] = channel.channel_id;
        channelElem.dataset['channelName'] = channel.channel_name;
        channelElem.dataset['genreId'] = channel.genre_id;
        channelElem.dataset['streamId'] = channel.stream_id;
        channelElem.toggleAttribute('selected', this.editMode && channel.channel_enabled)

        const genre = this.genres.find((g) => g.genre_id === channel.genre_id);
        channelElem.innerHTML = `
            <div class="channel-left">
                <span class="material-symbols-outlined">live_tv</span>
            </div>
            <div class="channel-details">
                <span class="channel-name">${channel.channel_name}</span>
                <span class="channel-group">${genre.genre_name}</span>
            </div>
            <div class="channel-right">
                <span class="material-symbols-outlined">hd</span>
                <span class="channel-number">${channel.channel_id}</span>
            </div>
        `

        channelElem.addEventListener('click', () => {
            if (this.editMode) {
                const selectedState = channelElem.hasAttribute('selected');
                channelElem.toggleAttribute('selected', !selectedState);
                const genreElem = this.querySelector('.search-container [name=genre]');
                if (genreElem.value === 'selected') {
                    this.searchChannelList();
                }

                if (typeof this.channelToggleCallback === 'function') {
                    this.channelToggleCallback(channel.channel_id);
                }
            } else {
                if (typeof this.channelClickCallback === 'function') {
                    this.channelClickCallback(channel.channel_id, channel.channel_name, channel.stream_id);
                }
            }
        });
        return channelElem;
    }
}

customElements.define('channel-list', ChannelList);