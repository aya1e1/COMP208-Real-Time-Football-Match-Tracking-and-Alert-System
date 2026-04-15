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

-- Performance indexes for user data
CREATE INDEX IF NOT EXISTS idx_UserPrefs_UserID   ON UserNotificationPreferences(UserID);
CREATE INDEX IF NOT EXISTS idx_UserPrefs_TeamID   ON UserNotificationPreferences(TeamID);
CREATE INDEX IF NOT EXISTS idx_Favourites_UserID  ON Favourites(UserID);
CREATE INDEX IF NOT EXISTS idx_Favourites_TeamID  ON Favourites(TeamID);
