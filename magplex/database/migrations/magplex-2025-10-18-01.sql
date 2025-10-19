create table if not exists channels (
    channel_id              int                         not null,
    device_uid              uuid                        not null references devices (device_uid) on delete cascade,
    creation_timestamp      timestamp with time zone    not null default current_timestamp,
    primary key (device_uid, channel_id)
);
create index if not exists channels_channel_idx on channels (channel_id);