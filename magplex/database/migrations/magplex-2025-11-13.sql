alter table channels alter column channel_name type varchar(256);

alter table devices add column referer varchar(128);
update devices set portal = 'http://' || portal || '/stalker_portal/server/load.php',
                   referer= 'http://' || portal || '/stalker_portal/c/';
alter table devices alter column referer set not null;
