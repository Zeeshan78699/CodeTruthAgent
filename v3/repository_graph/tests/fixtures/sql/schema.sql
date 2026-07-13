
-- Core schema definitions
CREATE TABLE users (
    id          NUMBER PRIMARY KEY,
    name        VARCHAR2(100) NOT NULL,
    email       VARCHAR2(200) UNIQUE,
    created_at  TIMESTAMP DEFAULT SYSDATE,
    is_active   NUMBER(1) DEFAULT 1
);

CREATE TABLE orders (
    id          NUMBER PRIMARY KEY,
    user_id     NUMBER REFERENCES users(id),
    total       NUMBER(10,2),
    status      VARCHAR2(20),
    created_at  TIMESTAMP DEFAULT SYSDATE
);

CREATE TABLE order_items (
    id          NUMBER PRIMARY KEY,
    order_id    NUMBER REFERENCES orders(id),
    product_id  NUMBER,
    quantity    NUMBER,
    price       NUMBER(10,2)
);

CREATE TABLE products (
    id          NUMBER PRIMARY KEY,
    name        VARCHAR2(200),
    price       NUMBER(10,2),
    stock       NUMBER
);
