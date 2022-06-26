/*Пользователь главный*/
create table if not exists user_vk(
    id serial primary key,
    user_id_vk varchar(20) not null,
    user_surname varchar(50) not null,
    user_first_name varchar(50) not null,
    user_city varchar(50) not null,
    user_age integer,
    user_gender integer
);


/*Объединненые пользователи*/
create table if not exists merging_users(
    id serial primary key,
    user_id_vk varchar(20) not null references user_vk(user_id_vk),
    merging_user_id varchar(20) not null unique,
    merging_surname varchar(50) not null,
    merging_first_name varchar(50) not null,
    merging_city varchar(50) not null,
    merging_age integer,
    merging_gender integer
);


/* Фото*/
create table if not exists photos(
    id serial primary key,
    photo_link text,
    merging_user_id varchar(20) not null references merging_users(merging_user_id),
    likes integer
);