create table if not exists payment_methods(
    id serial primary key,
    title text not null unique,
    description text not null,
    fee_percent real not null
);

insert into payment_methods (title, description, fee_percent) values
    ('CREDIT_CARD', 'Payment via credit card', 2.9),
    ('DEBIT_CARD', 'Payment via debit card', 1.5),
    ('UPI', 'Payment via UPI', 3.5),
    ('BANK_TRANSFER', 'Direct bank transfer', 0.0),
    ('CASH', 'Cash payment', 0.0);

alter table orders add constraint orders_payment_method_fk foreign key (payment_method) references payment_methods(title);

alter table products add column quantity int not null default 10;