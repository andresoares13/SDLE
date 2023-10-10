PRAGMA foreign_keys = ON;

CREATE TABLE User (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    password TEXT
);

CREATE TABLE List (
    id INTEGER PRIMARY KEY,
    password TEXT
);

CREATE TABLE Item (
    id INTEGER PRIMARY KEY,
    name TEXT,
    list_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY (list_id) REFERENCES List(id)
);
