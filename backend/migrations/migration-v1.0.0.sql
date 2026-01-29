begin;
create table if not exists schema_version(
    version text not null
);

create table if not exists users(
    id serial primary key,
    email text not null unique,
    password text not null,
    username text not null unique,
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
    reason text not null,
    description text not null
);

create table if not exists orders(
    id serial primary key,
    status text not null,
    paid_amount int not null,
    payment_method text not null,
    created_at timestamp default now(),
    delivered_at timestamp
);

create table if not exists order_items(
    id serial primary key,
    product_id int not null references products(id),
    order_id int not null references orders(id),
    quantity int not null default 1,
    unit_price int not null,
    tax_percent real not null
);

create table if not exists order_discounts(
    id serial primary key,
    order_item_id int not null references order_items(id),
    discount_id int not null references discounts(id)
);

create table if not exists order_refunds(
    id serial primary key,
    order_item_id int not null references order_items(id),
    refund_taxonomy_id int not null references refund_taxonomy(id),
    reason text not null,
    status text not null,
    amount int not null,
    evidence text,
    created_at timestamp default now(),
    processed_at timestamp
);

insert into refund_taxonomy(reason, description) values
    ('DAMAGED_ITEM', 'Product received in damaged or defective condition'),
    ('MISSING_ITEM', 'One or more items missing from the order'),
    ('LATE_DELIVERY', 'Order delivered after the promised delivery date'),
    ('DUPLICATE_CHARGE', 'Customer charged multiple times for the same order'),
    ('CANCELLATION', 'Order cancelled by customer or merchant'),
    ('RETURN_PICKUP_FAILED', 'Failed to pick up returned item from customer'),
    ('RETURN_TO_ORIGIN', 'Item returned to origin due to delivery failure'),
    ('PAYMENT_DEBITED_BUT_FAILED', 'Payment deducted but order not processed'),
    ('SERVICE_NOT_DELIVERED', 'Service ordered was not provided or delivered'),
    ('PRICE_ADJUSTMENT', 'Refund due to price difference or overcharge');

insert into schema_version values ('v1.0.0');
commit;