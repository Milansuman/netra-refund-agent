ALTER TABLE public.order_refunds DROP CONSTRAINT order_refunds_unique;
ALTER TABLE public.order_refunds ADD CONSTRAINT order_refunds_unique UNIQUE (order_item_id, thread_id);