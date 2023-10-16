PRAGMA foreign_keys = ON;

CREATE TABLE User (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    password TEXT
);

CREATE TABLE List (
    id INTEGER PRIMARY KEY,
    name TEXT,
    password TEXT UNIQUE
);

CREATE TABLE Item (
    id INTEGER PRIMARY KEY,
    name TEXT,
    list_key INTEGER,
    quantity INTEGER,
    FOREIGN KEY (list_key) REFERENCES List(password)
);

CREATE TABLE UserList (
    name TEXT,
    list_key TEXT,
    FOREIGN KEY (name) REFERENCES User(name) ON DELETE CASCADE,
    FOREIGN KEY (list_key) REFERENCES List(password) ON DELETE CASCADE
);

CREATE TABLE ListDeleteUpdate(
    username TEXT,
    list_key TEXT
);
    
    
    
