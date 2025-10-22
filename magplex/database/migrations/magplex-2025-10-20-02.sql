create table if not exists channel_guides (
    device_uid              uuid                        not null references devices (device_uid),
    channnel_id             int                         not null,
    title                   varchar(255)                not null,
    categories              varchar(128)[]              not null default [],
    description             varchar(512)                ,
    timestamp_range         tsrange                     not null,
    modified_timestamp      timestamp with time zone    not null default current_timestamp,
    creation_timestamp      timestamp with time zone    not null default current_timestamp,
    primary key (device_uid, channel_id, timestamp_range),
    exclude using gist (timestamp_range with &&)
);
