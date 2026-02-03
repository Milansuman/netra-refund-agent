-- Create a default user for testing/development
-- Password is 'password' hashed with SHA256
insert into users(id, email, password, username) 
values (1, 'demo@example.com', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'demo')
on conflict (id) do nothing;
