-- Users (for authentication system)
CREATE TABLE IF NOT EXISTS Users (
  UserID       INTEGER PRIMARY KEY AUTOINCREMENT,
  Username     VARCHAR(50)  NOT NULL UNIQUE,
  Email        VARCHAR(100) NOT NULL UNIQUE,
  PasswordHash VARCHAR(255) NOT NULL,
  CreatedDate  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User favourite teams
CREATE TABLE IF NOT EXISTS UserFavouriteTeams (
  UserID INTEGER NOT NULL,
  TeamID INTEGER NOT NULL,
  CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (UserID, TeamID),
  CONSTRAINT FK_FavTeams_User FOREIGN KEY (UserID) REFERENCES Users(UserID),
  CONSTRAINT FK_FavTeams_Team FOREIGN KEY (TeamID) REFERENCES Teams(TeamID)
);

-- User favourite players
CREATE TABLE IF NOT EXISTS UserFavouritePlayers (
  UserID INTEGER NOT NULL,
  PlayerID INTEGER NOT NULL,
  CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (UserID, PlayerID),
  CONSTRAINT FK_FavPlayers_User FOREIGN KEY (UserID) REFERENCES Users(UserID),
  CONSTRAINT FK_FavPlayers_Player FOREIGN KEY (PlayerID) REFERENCES Player(PlayerID)
);

-- User notification preferences
CREATE TABLE IF NOT EXISTS UserNotificationPreferences (
  PreferenceID        INTEGER PRIMARY KEY AUTOINCREMENT,
  UserID              INTEGER NOT NULL,
  TeamID              INT,
  NotifyGoals         BOOLEAN DEFAULT TRUE,
  NotifyCards         BOOLEAN DEFAULT TRUE,
  NotifySubstitutions BOOLEAN DEFAULT FALSE,
  CONSTRAINT FK_UserPrefs_User FOREIGN KEY (UserID) REFERENCES Users(UserID),
  CONSTRAINT FK_UserPrefs_Team FOREIGN KEY (TeamID) REFERENCES Teams(TeamID)
);

-- Event votes: users can like or dislike an event, but only one vote per event
CREATE TABLE IF NOT EXISTS EventVotes (
  VoteID       INTEGER PRIMARY KEY AUTOINCREMENT,
  UserID       INTEGER NOT NULL,
  FixtureID    INT NOT NULL,
  EventID      INT NOT NULL,
  VoteType     VARCHAR(10) NOT NULL,
  CreatedDate  DATETIME DEFAULT CURRENT_TIMESTAMP,
  UpdatedDate  DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT FK_EventVotes_User FOREIGN KEY (UserID) REFERENCES Users(UserID),
  CONSTRAINT FK_EventVotes_Event FOREIGN KEY (FixtureID, EventID) REFERENCES Events(FixtureID, EventID),
  CONSTRAINT CHK_EventVotes_Type CHECK (VoteType IN ('like', 'dislike')),
  CONSTRAINT UQ_EventVotes UNIQUE (UserID, FixtureID, EventID)
);

-- Performance indexes for user data
CREATE INDEX IF NOT EXISTS idx_UserFavTeams_UserID ON UserFavouriteTeams(UserID);
CREATE INDEX IF NOT EXISTS idx_UserFavTeams_TeamID ON UserFavouriteTeams(TeamID);
CREATE INDEX IF NOT EXISTS idx_UserFavPlayers_UserID ON UserFavouritePlayers(UserID);
CREATE INDEX IF NOT EXISTS idx_UserFavPlayers_PlayerID ON UserFavouritePlayers(PlayerID);
CREATE INDEX IF NOT EXISTS idx_UserPrefs_UserID   ON UserNotificationPreferences(UserID);
CREATE INDEX IF NOT EXISTS idx_UserPrefs_TeamID   ON UserNotificationPreferences(TeamID);
CREATE INDEX IF NOT EXISTS idx_EventVotes_Event   ON EventVotes(FixtureID, EventID);
CREATE INDEX IF NOT EXISTS idx_EventVotes_UserID  ON EventVotes(UserID);
