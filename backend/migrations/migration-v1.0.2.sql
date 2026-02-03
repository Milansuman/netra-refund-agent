-- Truncate tables before inserting mock data
truncate table order_refunds, order_discounts, order_items, orders, discounts, products, users restart identity cascade;

insert into users(id, email, password, username) 
values (1, 'demo@example.com', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'demo')
on conflict (id) do nothing;

-- Insert mock products
insert into products(title, description, price, tax_percent) values
    ('Wireless Headphones', 'Premium noise-cancelling wireless headphones', 1299900, 18.0),
    ('Smart Watch', 'Fitness tracking smart watch with heart rate monitor', 2499900, 18.0),
    ('USB-C Cable', 'High-speed USB-C charging cable 2m', 99900, 18.0),
    ('Laptop Stand', 'Adjustable aluminum laptop stand', 349900, 18.0),
    ('Mechanical Keyboard', 'RGB mechanical gaming keyboard', 899900, 18.0),
    ('Wireless Mouse', 'Ergonomic wireless mouse with precision tracking', 249900, 18.0),
    ('Phone Case', 'Shockproof protective phone case', 79900, 12.0),
    ('Screen Protector', 'Tempered glass screen protector', 59900, 12.0);

-- Insert mock discounts
insert into discounts(code, percent, amount) values
    ('WELCOME10', 10.0, null),
    ('FLAT500', null, 500),
    ('SUMMER20', 20.0, null),
    ('NEWYEAR15', 15.0, null);

-- Insert mock orders for user_id 1
insert into orders(status, paid_amount, payment_method, created_at, delivered_at, user_id) values
    ('DELIVERED', 1384800, 'UPI', '2025-12-15 10:30:00', '2025-12-18 14:20:00', 1),
    ('DELIVERED', 2654900, 'CREDIT_CARD', '2025-12-20 15:45:00', '2025-12-23 11:30:00', 1),
    ('DELIVERED', 1504600, 'UPI', '2026-01-10 09:15:00', '2026-01-13 16:45:00', 1),
    ('PROCESSING', 472900, 'DEBIT_CARD', '2026-01-25 14:20:00', null, 1);

-- Insert order items for order 1
insert into order_items(product_id, order_id, quantity, unit_price, tax_percent) values
    (1, 1, 1, 1299900, 18.0),  -- Wireless Headphones
    (3, 1, 1, 99900, 18.0);     -- USB-C Cable

-- Insert order discounts for order 1
insert into order_discounts(order_item_id, discount_id) values
    (1, 1);  -- WELCOME10 on headphones

-- Insert order items for order 2
insert into order_items(product_id, order_id, quantity, unit_price, tax_percent) values
    (2, 2, 1, 2499900, 18.0),  -- Smart Watch
    (6, 2, 1, 249900, 18.0);   -- Wireless Mouse

-- Insert order discounts for order 2
insert into order_discounts(order_item_id, discount_id) values
    (3, 2);  -- FLAT500 on smart watch

-- Insert order items for order 3
insert into order_items(product_id, order_id, quantity, unit_price, tax_percent) values
    (5, 3, 1, 899900, 18.0),   -- Mechanical Keyboard
    (4, 3, 1, 349900, 18.0),   -- Laptop Stand
    (7, 3, 2, 79900, 12.0);    -- Phone Cases x2

-- Insert order discounts for order 3
insert into order_discounts(order_item_id, discount_id) values
    (5, 3);  -- SUMMER20 on keyboard

-- Insert order items for order 4
insert into order_items(product_id, order_id, quantity, unit_price, tax_percent) values
    (4, 4, 1, 349900, 18.0),   -- Laptop Stand
    (8, 4, 2, 59900, 12.0);    -- Screen Protectors x2

-- Insert mock refunds
insert into order_refunds(order_item_id, refund_taxonomy_id, reason, status, amount, evidence, created_at, processed_at) values
    (1, 1, 'Left earpiece stopped working after 2 days of use', 'APPROVED', 1169900, 'Photo of defective product and purchase receipt attached', '2025-12-19 10:00:00', '2025-12-20 14:30:00'),
    (6, 2, 'Second phone case was missing from the package', 'APPROVED', 89500, 'Video of unboxing showing only 1 case', '2026-01-14 09:30:00', '2026-01-15 11:00:00'),
    (3, 8, 'Payment was debited twice for this order', 'PROCESSING', 2949800, 'Bank statement showing duplicate charges', '2025-12-21 16:45:00', null);
