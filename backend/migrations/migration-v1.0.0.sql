create table if not exists users(
    id serial primary key,
    email text not null,
    password text not null,
    username text not null,
    created_at timestamp default now()
);

create table if not exists products(
    id serial primary key,
    title text not null,
    description text,
    price int not null,
    tax_percent real not null
);

create table if not exists discounts(
    id serial primary key,
    code text not null,
    percent real,
    amount int
);

create table if not exists refund_taxonomy(
    id serial primary key,
    reason text not null
);

create table if not exists orders(
    id serial primary key,
    user_id int not null references users(id),
    product_id int not null references products(id),
    paid_amount int not null
);

create table if not exists order_discounts(
    id serial primary key,
    order_id int not null references orders(id),
    discount_id int not null references discounts(id)
);

create table if not exists order_refunds(
    id serial primary key,
    order_id int not null references orders(id),
    refund_taxonomy int not null references refund_taxonomy(id),
    reason text not null,
    amount int not null
);

create table if not exists chats(
    id serial primary key,
    user_id int not null references users(id)
);

create table if not exists chat_messages(
    id serial primary key,
    chat_id int not null references chats(id),
    content text not null,
    role text not null
);

insert into refund_taxonomy(reason) values 
    ('DAMAGED_ITEM'),
    ('MISSING_ITEM'),
    ('LATE_DELIVERY'),
    ('DUPLICATE_CHARGE'),
    ('CANCELLATION'),
    ('RETURN_PICKUP_FAILED'),
    ('RETURN_TO_ORIGIN'),
    ('PAYMENT_DEBITED_BUT_FAILED'),
    ('SERVICE_NOT_DELIVERED'),
    ('PRICE_ADJUSTMENT');