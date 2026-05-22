ALTER TABLE invitations ADD COLUMN game_id INTEGER REFERENCES games(id);
