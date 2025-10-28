create extension if not exists pgcrypto;


---------------------- Migrations ----------------------
create table if not exists migrations (
    migration_name          varchar(128)                not null primary key,
    creation_timestamp      timestamp with time zone    not null default current_timestamp
);



-------------------- Users & Session -------------------
create table if not exists users (
    user_uid                uuid                        not null primary key default gen_random_uuid(),
    username                varchar(128)                not null,
    password                varchar(128)                not null,
    is_admin                boolean                     not null default false,
    modified_timestamp      timestamp with time zone    not null default current_timestamp,
    creation_timestamp      timestamp with time zone    not null default current_timestamp
);
create unique index if not exists users_email_idx on users (username);

insert into users (username, password, is_admin)
    select 'admin', crypt('admin', gen_salt('bf')), true
    where not exists (select 1 from users where is_admin = true);


create table if not exists user_sessions (
    session_uid             uuid                        not null primary key default gen_random_uuid(),
    user_uid                uuid                        not null references users (user_uid) on delete cascade,
    ip_address              inet                        not null,
    expiration_timestamp    timestamp with time zone    not null,
    creation_timestamp      timestamp with time zone    not null default current_timestamp
);
create index if not exists user_sessions_user_idx on user_sessions (session_uid);



----------------------- Devices -----------------------
create table if not exists devices (
    device_uid              uuid                        not null primary key default gen_random_uuid(),
    user_uid                uuid                        not null references users (user_uid) on delete cascade,
    mac_address             macaddr                     not null,
    device_id1              varchar(128)                ,
    device_id2              varchar(128)                ,
    signature               varchar(128)                ,
    portal                  varchar(128)                not null,
    language                varchar(32)                 not null,
    timezone                varchar(64)                 not null,
    modified_timestamp      timestamp with time zone    not null default current_timestamp,
    creation_timestamp      timestamp with time zone    not null default current_timestamp
);
create unique index if not exists devices_user_uid_idx on devices (user_uid);
create unique index if not exists devices_mac_address on devices (mac_address);



------------------- Device Operations -----------------
create table if not exists genres (
    device_uid              uuid                        not null references devices (device_uid),
    genre_id                int                         not null,
    genre_name              varchar(128)                not null,
    creation_timestamp      timestamp with time zone    not null default current_timestamp,
    primary key (device_uid, genre_id)
);


create table if not exists channels (
    channel_id              int                         not null,
    channel_number          int                         not null,
    channel_name            varchar(128)                not null,
    channel_hd              boolean                     not null default false,
    channel_enabled         boolean                     not null default true,
    genre_id                int                         not null references genres (genre_id),
    stream_id               int                         not null,
    device_uid              uuid                        not null references devices (device_uid) on delete cascade,
    creation_timestamp      timestamp with time zone    not null default current_timestamp,
    primary key (device_uid, channel_id),
    foreign key (device_uid, genre_id) references genres (device_uid, genre_id)
);
create index if not exists channels_device_uid_channel_number_idx on channels (device_uid, channel_number);
create index if not exists channels_device_uid_genre_id_idx on channels (device_uid, genre_id);
create index if not exists channels_channel_idx on channels (channel_id);


create table if not exists channel_guides (
    device_uid              uuid                        not null references devices (device_uid),
    channel_id              int                         not null,
    title                   varchar(255)                not null,
    categories              varchar(128)[]              not null default '{}',
    description             varchar(512)                ,
    timestamp_range         tsrange                     not null,
    modified_timestamp      timestamp with time zone    not null default current_timestamp,
    creation_timestamp      timestamp with time zone    not null default current_timestamp,
    primary key (device_uid, channel_id, timestamp_range),
    exclude using gist (timestamp_range with &&)
);
