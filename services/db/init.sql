CREATE TABLE IF NOT EXISTS product (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    quantity INTEGER DEFAULT 100
);

INSERT INTO product (name) VALUES ('Produto A'), ('Produto B') ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS "order" (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES product(id),
    quantity INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending'
);