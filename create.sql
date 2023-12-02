PRAGMA foreign_keys = ON;

CREATE TABLE User (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    password TEXT
);

CREATE TABLE List (
    id INTEGER PRIMARY KEY,
    name TEXT,
    shared INTEGER DEFAULT 0,
    password TEXT UNIQUE
);

CREATE TABLE Item (
    id INTEGER PRIMARY KEY,
    name TEXT,
    list_key INTEGER,
    quantity INTEGER,
    FOREIGN KEY (list_key) REFERENCES List(password) ON DELETE CASCADE
);

CREATE TABLE UserList (
    name TEXT,
    list_key TEXT,
    FOREIGN KEY (name) REFERENCES User(name) ON DELETE CASCADE,
    FOREIGN KEY (list_key) REFERENCES List(password) ON DELETE CASCADE
);

CREATE TABLE ListDeleteUpdate(
    username TEXT,
    list_key TEXT,
    FOREIGN KEY (list_key) REFERENCES List(password) ON DELETE CASCADE,
    FOREIGN KEY (username) REFERENCES User(name) ON DELETE CASCADE
);

CREATE TABLE ItemChangeUpdate(
    username TEXT,
    list_key TEXT,
    item TEXT,
    FOREIGN KEY (list_key) REFERENCES List(password) ON DELETE CASCADE,
    FOREIGN KEY (username) REFERENCES User(name) ON DELETE CASCADE
    
);

CREATE TABLE ItemIncreaseDict(
    username TEXT,
    list_key TEXT,
    item TEXT,
    quantity INTEGER,
    FOREIGN KEY (list_key) REFERENCES List(password) ON DELETE CASCADE,
    FOREIGN KEY (username) REFERENCES User(name) ON DELETE CASCADE
);

CREATE TABLE ItemDecreaseDict(
    username TEXT,
    list_key TEXT,
    item TEXT,
    quantity INTEGER,
    FOREIGN KEY (list_key) REFERENCES List(password) ON DELETE CASCADE,
    FOREIGN KEY (username) REFERENCES User(name) ON DELETE CASCADE
);

CREATE TABLE ServerListAssign(
    server INTEGER,
    list_key TEXT,
    FOREIGN KEY (list_key) REFERENCES List(password) ON DELETE CASCADE
);


CREATE TABLE ServerListChangeUpdate(
    server INTEGER,
    list_key TEXT,
    FOREIGN KEY (list_key) REFERENCES List(password) ON DELETE CASCADE
);



CREATE TABLE ServerItemChangeUpdate(
    server INTEGER,
    list_key TEXT,
    FOREIGN KEY (list_key) REFERENCES List(password) ON DELETE CASCADE
);

CREATE TABLE ServerUserChangeUpdate(
    server INTEGER,
    name TEXT,
    password TEXT,
    change INTEGER
);













    
    
    
