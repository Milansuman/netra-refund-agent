-- Add stock tracking to products table
alter table products add column if not exists stock_quantity int not null default 0;

-- Update existing products with some default stock
update products set stock_quantity = 100 where stock_quantity = 0;
