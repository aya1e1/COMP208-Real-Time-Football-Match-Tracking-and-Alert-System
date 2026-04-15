PRAGMA foreign_keys = ON;

-- League
CREATE TABLE IF NOT EXISTS League (
  LeagueID INT PRIMARY KEY,
  Name     VARCHAR(50) NOT NULL,
  Country  VARCHAR(50),
  LogoURL  VARCHAR(255)
);

-- Teams
CREATE TABLE IF NOT EXISTS Teams (
  TeamID       INT PRIMARY KEY,
  Name         VARCHAR(50) NOT NULL,
  Abbreviation VARCHAR(10),
  City         VARCHAR(50),
  Stadium      VARCHAR(50)
);

-- Seasons
CREATE TABLE IF NOT EXISTS Seasons (
  LeagueID  INT NOT NULL,
  Year      INT NOT NULL,
  StartDate DATE,
  EndDate   DATE,
  Current   INT DEFAULT 0,
  CONSTRAINT PK_Seasons PRIMARY KEY (LeagueID, Year),
  CONSTRAINT FK_Seasons_League FOREIGN KEY (LeagueID) REFERENCES League(LeagueID)
);

-- SeasonTeams: which teams participate in a given season
CREATE TABLE IF NOT EXISTS SeasonTeams (
  TeamID   INT NOT NULL,
  LeagueID INT NOT NULL,
  Year     INT NOT NULL,
  CONSTRAINT PK_SeasonTeams PRIMARY KEY (LeagueID, Year, TeamID),
  CONSTRAINT FK_SeasonTeams_Team   FOREIGN KEY (TeamID)   REFERENCES Teams(TeamID),
  CONSTRAINT FK_SeasonTeams_Season FOREIGN KEY (LeagueID, Year) REFERENCES Seasons(LeagueID, Year)
);

-- League Table / Standings
CREATE TABLE IF NOT EXISTS LeagueTable (
  LeagueID INT NOT NULL,
  Year     INT NOT NULL,
  TeamID   INT NOT NULL,
  Position INT,
  Points   INT DEFAULT 0,
  Played   INT DEFAULT 0,
  Won      INT DEFAULT 0,
  Lost     INT DEFAULT 0,
  GF       INT DEFAULT 0,
  GA       INT DEFAULT 0,
  PRIMARY KEY (LeagueID, Year, TeamID),
  CONSTRAINT FK_LeagueTable_Teams  FOREIGN KEY (TeamID)   REFERENCES Teams(TeamID),
  CONSTRAINT FK_LeagueTable_Season FOREIGN KEY (LeagueID, Year) REFERENCES Seasons(LeagueID, Year)
);

-- Players
CREATE TABLE IF NOT EXISTS Player (
  PlayerID     INT PRIMARY KEY,
  Name         VARCHAR(100) NOT NULL,
  MainPosition VARCHAR(50),
  DateOfBirth  DATE,
  Nationality  VARCHAR(50)
);

-- PlayerTeam
CREATE TABLE IF NOT EXISTS PlayerTeam (
  PlayerID      INT NOT NULL,
  TeamID        INT NOT NULL,
  Shirt_Number  INT,
  Contract_Type VARCHAR(50),
  PRIMARY KEY (PlayerID, TeamID),
  CONSTRAINT FK_PlayerTeam_Player FOREIGN KEY (PlayerID) REFERENCES Player(PlayerID),
  CONSTRAINT FK_PlayerTeam_Team   FOREIGN KEY (TeamID)   REFERENCES Teams(TeamID)
);

-- Fixtures
CREATE TABLE IF NOT EXISTS Fixtures (
  FixtureID  INT PRIMARY KEY,
  LeagueID   INT NOT NULL,
  Year       INT,
  HomeTeamID INT NOT NULL,
  AwayTeamID INT NOT NULL,
  Location   VARCHAR(100),
  MatchDate  DATETIME NOT NULL,
  HomeScore  INT DEFAULT 0,
  AwayScore  INT DEFAULT 0,
  Status    VARCHAR(10) DEFAULT 'NS',
  Elapsed   INT DEFAULT 0,
  CONSTRAINT FK_Fixtures_League   FOREIGN KEY (LeagueID)   REFERENCES League(LeagueID),
  CONSTRAINT FK_Fixtures_Season   FOREIGN KEY (LeagueID, Year) REFERENCES Seasons(LeagueID, Year),
  CONSTRAINT FK_Fixtures_HomeTeam FOREIGN KEY (HomeTeamID) REFERENCES Teams(TeamID),
  CONSTRAINT FK_Fixtures_AwayTeam FOREIGN KEY (AwayTeamID) REFERENCES Teams(TeamID),
  CONSTRAINT CHK_Fixtures_Score         CHECK (HomeScore >= 0 AND AwayScore >= 0),
  CONSTRAINT CHK_Fixtures_DifferentTeams CHECK (HomeTeamID <> AwayTeamID)
);

-- Match Events (goals, cards, substitutions)
CREATE TABLE IF NOT EXISTS Events (
  FixtureID   INT NOT NULL,
  EventID     INT NOT NULL,
  PlayerID    INT,
  AssistPlayerID INT,
  TeamID      INT,
  EventType   VARCHAR(50),
  Detail     VARCHAR(255),
  EventMinute INT,
  ExtraMinute INT DEFAULT 0,
  CONSTRAINT PK_Events         PRIMARY KEY (FixtureID, EventID),
  CONSTRAINT FK_Events_Fixture FOREIGN KEY (FixtureID) REFERENCES Fixtures(FixtureID),
  CONSTRAINT FK_Events_Team    FOREIGN KEY (TeamID)    REFERENCES Teams(TeamID)
);

-- Users (for authentication system)
CREATE TABLE IF NOT EXISTS Users (
  UserID       INTEGER PRIMARY KEY AUTOINCREMENT,
  Username     VARCHAR(50)  NOT NULL UNIQUE,
  Email        VARCHAR(100) NOT NULL UNIQUE,
  PasswordHash VARCHAR(255) NOT NULL,
  CreatedDate  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User Favourite Teams
CREATE TABLE IF NOT EXISTS UserFavouriteTeams (
  UserID INTEGER NOT NULL,
  TeamID INTEGER NOT NULL,
  PRIMARY KEY (UserID, TeamID),
  CONSTRAINT FK_FavTeams_User FOREIGN KEY (UserID) REFERENCES Users(UserID),
  CONSTRAINT FK_FavTeams_Team FOREIGN KEY (TeamID) REFERENCES Teams(TeamID)
);

-- User Notification Preferences
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

-- API response cache
CREATE TABLE IF NOT EXISTS Cache (
  CacheKey  TEXT PRIMARY KEY,
  Data      TEXT NOT NULL,
  FetchedAt TEXT NOT NULL DEFAULT (datetime('now')),
  ExpiresAt TEXT NOT NULL
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_Fixtures_LeagueID  ON Fixtures(LeagueID);
CREATE INDEX IF NOT EXISTS idx_Fixtures_MatchDate ON Fixtures(MatchDate);
CREATE INDEX IF NOT EXISTS idx_Fixtures_Status    ON Fixtures(Status);
CREATE INDEX IF NOT EXISTS idx_Events_FixtureID   ON Events(FixtureID);
CREATE INDEX IF NOT EXISTS idx_Events_EventType   ON Events(EventType);
CREATE INDEX IF NOT EXISTS idx_PlayerTeam_TeamID  ON PlayerTeam(TeamID);
CREATE INDEX IF NOT EXISTS idx_UserPrefs_UserID   ON UserNotificationPreferences(UserID);
CREATE INDEX IF NOT EXISTS idx_UserPrefs_TeamID   ON UserNotificationPreferences(TeamID);
CREATE INDEX IF NOT EXISTS idx_Favourites_UserID  ON Favourites(UserID);
CREATE INDEX IF NOT EXISTS idx_Favourites_TeamID  ON Favourites(TeamID);
CREATE INDEX IF NOT EXISTS idx_Cache_ExpiresAt    ON Cache(ExpiresAt);
