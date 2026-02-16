create table if not exists tickets(
    id serial primary key,
    order_id int not null references orders(id),
    user_id int not null references users(id),
    title text not null,
    description text
);