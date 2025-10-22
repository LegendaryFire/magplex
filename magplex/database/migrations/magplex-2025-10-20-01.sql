create table if not exists genres (
    device_uid              uuid                        not null references devices (device_uid),
    genre_id                int                         not null,
    genre_number            int                         not null,
    genre_name              varchar(128)                not null,
    creation_timestamp      timestamp with time zone    not null default current_timestamp,
    primary key (device_uid, genre_id)
);

alter table channels add column channel_number int not null;
alter table channels add column channel_name varchar(128) not null;
alter table channels add column channel_hd boolean not null default false;
alter table channels add column channel_enabled boolean not null default true;
alter table channels add column genre_id int not null;
alter table channels add constraint channels_device_uid_genre_id_fkey foreign key (device_uid, genre_id)
    references genres (device_uid, genre_id) on delete cascade;
alter table channels add column stream_id int not null;

create index if not exists channels_device_uid_channel_number_idx on channels (device_uid, channel_number);
create index if not exists channels_device_uid_genre_id_idx on channels (device_uid, genre_id);
