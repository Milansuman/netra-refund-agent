create table if not exists sessions(
    id serial primary key,
    user_id int not null references users(id)
);