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
  PRIMARY KEY (UserID, TeamID),
  CONSTRAINT FK_FavTeams_User FOREIGN KEY (UserID) REFERENCES Users(UserID),
  CONSTRAINT FK_FavTeams_Team FOREIGN KEY (TeamID) REFERENCES Teams(TeamID)
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

-- Favourites: users can follow teams and/or players
CREATE TABLE IF NOT EXISTS Favourites (
  FavouriteID INTEGER PRIMARY KEY AUTOINCREMENT,
  UserID      INTEGER NOT NULL,
  TeamID      INT,
  PlayerID    INT,
  CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT FK_Favourites_User   FOREIGN KEY (UserID)   REFERENCES Users(UserID),
  CONSTRAINT FK_Favourites_Team   FOREIGN KEY (TeamID)   REFERENCES Teams(TeamID),
  CONSTRAINT FK_Favourites_Player FOREIGN KEY (PlayerID) REFERENCES Player(PlayerID),
  CONSTRAINT CHK_Favourites_HasTarget CHECK (TeamID IS NOT NULL OR PlayerID IS NOT NULL),
  CONSTRAINT UQ_Favourites UNIQUE (UserID, TeamID, PlayerID)
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
CREATE INDEX IF NOT EXISTS idx_UserPrefs_UserID   ON UserNotificationPreferences(UserID);
CREATE INDEX IF NOT EXISTS idx_UserPrefs_TeamID   ON UserNotificationPreferences(TeamID);
CREATE INDEX IF NOT EXISTS idx_Favourites_UserID  ON Favourites(UserID);
CREATE INDEX IF NOT EXISTS idx_Favourites_TeamID  ON Favourites(TeamID);
CREATE INDEX IF NOT EXISTS idx_EventVotes_Event   ON EventVotes(FixtureID, EventID);
CREATE INDEX IF NOT EXISTS idx_EventVotes_UserID  ON EventVotes(UserID);
