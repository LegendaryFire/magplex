from . import device, users


def create_database(conn):
    cursor = conn.cursor()
    query = """
        create extension if not exists pgcrypto;


        create table if not exists users (
            user_uid                uuid                        not null primary key default gen_random_uuid(),
            username                varchar(128)                not null,
            password                varchar(128)                not null,
            modified_timestamp      timestamp with time zone    not null default current_timestamp,
            creation_timestamp      timestamp with time zone    not null default current_timestamp
        );
        create unique index if not exists users_email_idx on users (username);
            
        insert into users (username, password) values ('admin',  crypt('admin', gen_salt('bf'))) on conflict do nothing;


        create table if not exists user_sessions (
            session_uid             uuid                        not null primary key default gen_random_uuid(),
            user_uid                uuid                        not null references users (user_uid) on delete cascade,
            ip_address              inet                        not null,
            expiration_timestamp    timestamp with time zone    not null,
            creation_timestamp      timestamp with time zone    not null default current_timestamp
        );
        create index if not exists user_sessions_user_idx on user_sessions (session_uid);


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


        create table if not exists migrations (
            migration_id            int                         not null primary key,
            creation_timestamp      timestamp with time zone    not null default current_timestamp
        );
    """
    cursor.execute(query)
    conn.commit()