-- Clear existing data
truncate table order_refunds, order_discounts, order_items, orders, discounts, products, users restart identity cascade;

-- Insert demo user
insert into users(id, email, password, username) 
values (1, 'demo@example.com', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'demo')
on conflict (id) do nothing;

-- Insert products with reasonable Indian prices (in paise)
insert into products(title, description, price, tax_percent) values
    ('Wireless Headphones', 'Premium noise-cancelling wireless headphones', 299900, 18.0),      -- ₹2,999
    ('Smart Watch', 'Fitness tracking smart watch with heart rate monitor', 799900, 18.0),     -- ₹7,999
    ('USB-C Cable', 'High-speed USB-C charging cable 2m', 29900, 18.0),                        -- ₹299
    ('Laptop Stand', 'Adjustable aluminum laptop stand', 149900, 18.0),                        -- ₹1,499
    ('Mechanical Keyboard', 'RGB mechanical gaming keyboard', 349900, 18.0),                   -- ₹3,499
    ('Wireless Mouse', 'Ergonomic wireless mouse with precision tracking', 99900, 18.0),       -- ₹999
    ('Phone Case', 'Shockproof protective phone case', 39900, 12.0),                           -- ₹399
    ('Screen Protector', 'Tempered glass screen protector', 19900, 12.0);                      -- ₹199

-- Insert orders (one product each)
-- Calculated amounts: price × (1 + tax_percent/100)
insert into orders(status, paid_amount, payment_method, created_at, delivered_at, user_id) values
    ('DELIVERED', FLOOR(299900 * 1.18), 'CREDIT_CARD', '2025-12-15 10:30:00', '2025-12-18 14:20:00', 1),       -- Headphones: ₹2,999 + 18% tax = ₹3,538.82
    ('DELIVERED', FLOOR(799900 * 1.18), 'CREDIT_CARD', '2025-12-20 15:45:00', '2025-12-23 11:30:00', 1), -- Smart Watch: ₹7,999 + 18% tax = ₹9,438.82
    ('DELIVERED', FLOOR(149900 * 1.18), 'CREDIT_CARD', '2026-01-10 09:15:00', '2026-01-13 16:45:00', 1),       -- Laptop Stand: ₹1,499 + 18% tax = ₹1,768.82
    ('PROCESSING', FLOOR(349900 * 1.18), 'DEBIT_CARD', '2026-01-25 14:20:00', null, 1);                -- Keyboard: ₹3,499 + 18% tax = ₹4,128.82

-- Insert order items (one product per order)
insert into order_items(product_id, order_id, quantity, unit_price, tax_percent) values
    (1, 1, 1, 299900, 18.0),  -- Wireless Headphones
    (2, 2, 1, 799900, 18.0),  -- Smart Watch
    (4, 3, 1, 149900, 18.0),  -- Laptop Stand
    (5, 4, 1, 349900, 18.0);  -- Mechanical Keyboard

-- Insert refunds
insert into order_refunds(order_item_id, refund_taxonomy_id, reason, status, amount, evidence, created_at, processed_at) values
    (1, 1, 'Left earpiece stopped working after 2 days of use', 'APPROVED', FLOOR(299900 * 1.18), 'Photo of defective product and purchase receipt attached', '2025-12-19 10:00:00', '2025-12-20 14:30:00'),
    (3, 2, 'Product arrived damaged with scratches on the surface', 'APPROVED', FLOOR(149900 * 1.18), 'Photos showing damaged product', '2026-01-14 09:30:00', '2026-01-15 11:00:00'),
    (2, 8, 'Payment was debited twice for this order', 'PROCESSING', FLOOR(799900 * 1.18), 'Bank statement showing duplicate charges', '2025-12-21 16:45:00', null);
