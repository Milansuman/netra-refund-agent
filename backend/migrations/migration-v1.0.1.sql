create table if not exists sessions(
    id text primary key,
    user_id int not null references users(id)
);