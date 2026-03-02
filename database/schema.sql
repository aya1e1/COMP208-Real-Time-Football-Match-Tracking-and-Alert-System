-- League
CREATE TABLE League (
  LeagueID INT PRIMARY KEY,
  Name VARCHAR(50) NOT NULL
);

-- Teams
CREATE TABLE Teams (
  TeamID INT PRIMARY KEY,
  Name VARCHAR(50) NOT NULL,
  Abbreviation VARCHAR(10),
  City VARCHAR(50),
  LeagueID INT NOT NULL,
  CONSTRAINT FK_Teams_League FOREIGN KEY (LeagueID) REFERENCES League(LeagueID)
);

-- Seasons
CREATE TABLE Seasons (
  SeasonID INT PRIMARY KEY,
  LeagueID INT NOT NULL,
  Name VARCHAR(50), -- idk if we need name here bc league already has a name
  StartDate DATE,
  EndDate DATE,
  CONSTRAINT FK_Seasons_League FOREIGN KEY (LeagueID) REFERENCES League(LeagueID)
);

-- LeagueTable
CREATE TABLE LeagueTable (
  LeagueID INT NOT NULL,
  TeamID INT NOT NULL,
  Position INT, 
  Points INT,
  Played INT,
  GF INT,
  GA INT,
  PRIMARY KEY (LeagueID, TeamID),
  CONSTRAINT FK_LeagueTable_Teams FOREIGN KEY (TeamID) REFERENCES Teams(TeamID), 
  CONSTRAINT FK_LeagueTable_League FOREIGN KEY (LeagueID) REFERENCES League(LeagueID)
);

-- Players
CREATE TABLE Player (
  PlayerID INT PRIMARY KEY,
  Name VARCHAR(100) NOT NULL,
  MainPosition VARCHAR(50),
  DateOfBirth DATE,
  Nationality VARCHAR(50)
);

-- PlayerTeam
CREATE TABLE PlayerTeam (
  PlayerID INT NOT NULL,
  TeamID INT NOT NULL,
  Shirt_Number INT,
  Contract_Type VARCHAR(50),
  PRIMARY KEY (PlayerID, TeamID),
  CONSTRAINT FK_PlayerTeam_Player FOREIGN KEY (PlayerID) REFERENCES Player(PlayerID),
  CONSTRAINT FK_PlayerTeam_Team FOREIGN KEY (TeamID) REFERENCES Teams(TeamID)
);

-- Fixtures
CREATE TABLE Fixtures (
  FixtureID INT PRIMARY KEY,
  LeagueID INT NOT NULL,
  HomeTeam INT NOT NULL,
  AwayTeam INT NOT NULL,
  Location VARCHAR(100),
  MatchDate DATETIME NOT NULL,
  Completed BOOLEAN DEFAULT FALSE,
  HomeScore INT DEFAULT 0,
  AwayScore INT DEFAULT 0,
  CONSTRAINT FK_Fixtures_League FOREIGN KEY (LeagueID) REFERENCES League(LeagueID),
  CONSTRAINT FK_Fixtures_HomeTeam FOREIGN KEY (HomeTeam) REFERENCES Teams(TeamID),
  CONSTRAINT FK_Fixtures_AwayTeam FOREIGN KEY (AwayTeam) REFERENCES Teams(TeamID),
  CONSTRAINT CHK_Fixtures_Score CHECK (HomeScore >= 0 AND AwayScore >= 0),
  CONSTRAINT CHK_Fixtures_DifferentTeams CHECK (HomeTeam <> AwayTeam)
);

-- Events
CREATE TABLE Events (
  FixtureID INT NOT NULL,
  EventID INT NOT NULL, 
  PlayerID INT,
  TeamID INT NOT NULL,
  EventType VARCHAR(50),
  Description VARCHAR(255),
  EventMinutes INT,
  CONSTRAINT Pk_Events PRIMARY KEY (FixtureID, EventID),
  CONSTRAINT FK_Events_Player FOREIGN KEY (PlayerID) REFERENCES Player(PlayerID),
  CONSTRAINT FK_Events_Fixture FOREIGN KEY (FixtureID) REFERENCES Fixtures(FixtureID),
  CONSTRAINT FK_Events_Team FOREIGN KEY (TeamID) REFERENCES Teams(TeamID)
);

-- User (for authentication system)
CREATE TABLE Users (
  UserID INT PRIMARY KEY AUTO_INCREMENT,
  Username VARCHAR(50) NOT NULL UNIQUE,
  Email VARCHAR(100) NOT NULL UNIQUE,
  PasswordHash VARCHAR(255) NOT NULL,
  CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User Notification Preferences
CREATE TABLE UserNotificationPreferences (
  PreferenceID INT PRIMARY KEY AUTO_INCREMENT,
  UserID INT NOT NULL,
  TeamID INT,
  NotifyGoals BOOLEAN DEFAULT TRUE,
  NotifyCards BOOLEAN DEFAULT TRUE,
  NotifySubstitutions BOOLEAN DEFAULT FALSE,
  CONSTRAINT FK_UserPrefs_User FOREIGN KEY (UserID) REFERENCES Users(UserID),
  CONSTRAINT FK_UserPrefs_Team FOREIGN KEY (TeamID) REFERENCES Teams(TeamID)
);

-- Performance Indexes
CREATE INDEX idx_Fixtures_LeagueID ON Fixtures(LeagueID);
CREATE INDEX idx_Fixtures_MatchDate ON Fixtures(MatchDate);
CREATE INDEX idx_Events_FixtureID ON Events(FixtureID);
CREATE INDEX idx_Events_EventType ON Events(EventType);
CREATE INDEX idx_PlayerTeam_TeamID ON PlayerTeam(TeamID);
CREATE INDEX idx_UserPrefs_UserID ON UserNotificationPreferences(UserID);
CREATE INDEX idx_UserPrefs_TeamID ON UserNotificationPreferences(TeamID);
