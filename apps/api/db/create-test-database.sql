-- Runs once, when the api-db volume is first created: a separate database for the tests.
-- The tests drop every table first, so they must never share a database with the app.
CREATE DATABASE playground_test;
-- The API role is not made here: migration 0002 creates it, on the dev and the test database alike (ADR 0012).
