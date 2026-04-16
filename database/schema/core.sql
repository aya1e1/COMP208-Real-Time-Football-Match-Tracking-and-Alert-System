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
  LogoURL      VARCHAR(255),
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
  Description VARCHAR(255),
  Points   INT DEFAULT 0,
  Played   INT DEFAULT 0,
  Won      INT DEFAULT 0,
  Drawn    INT DEFAULT 0,
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
  FirstName    VARCHAR(50),
  LastName     VARCHAR(50),
  Name         VARCHAR(100) NOT NULL,
  MainPosition VARCHAR(50),
  DateOfBirth  DATE,
  PlaceOfBirth VARCHAR(100),
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
  PlayerName  VARCHAR(100),
  AssistPlayerID INT,
  AssistPlayerName VARCHAR(100),
  TeamID      INT,
  EventType   VARCHAR(50),
  Detail      VARCHAR(255),
  Comments    VARCHAR(255),
  EventMinute INT,
  ExtraMinute INT DEFAULT 0,
  CONSTRAINT PK_Events         PRIMARY KEY (FixtureID, EventID),
  CONSTRAINT FK_Events_Fixture FOREIGN KEY (FixtureID) REFERENCES Fixtures(FixtureID),
  CONSTRAINT FK_Events_Team    FOREIGN KEY (TeamID)    REFERENCES Teams(TeamID)
);

-- Fixture statistics: one row per fixture/team pair
CREATE TABLE IF NOT EXISTS FixtureStatistics (
  FixtureID         INT NOT NULL,
  TeamID            INT NOT NULL,
  ShotsOnGoal       INT,
  ShotsOffGoal      INT,
  TotalShots        INT,
  BlockedShots      INT,
  ShotsInsideBox    INT,
  ShotsOutsideBox   INT,
  Fouls             INT,
  CornerKicks       INT,
  Offsides          INT,
  BallPossession    DECIMAL(5, 2),
  YellowCards       INT,
  RedCards          INT,
  GoalkeeperSaves   INT,
  TotalPasses       INT,
  PassesAccurate    INT,
  PassesPercentage  DECIMAL(5, 2),
  ExpectedGoals     DECIMAL(10, 2),
  GoalsPrevented    INT,
  CONSTRAINT PK_FixtureStatistics PRIMARY KEY (FixtureID, TeamID),
  CONSTRAINT FK_FixtureStatistics_Fixture FOREIGN KEY (FixtureID) REFERENCES Fixtures(FixtureID),
  CONSTRAINT FK_FixtureStatistics_Team    FOREIGN KEY (TeamID)    REFERENCES Teams(TeamID)
);

-- Team statistics: one row per league/season/team
CREATE TABLE IF NOT EXISTS TeamStatistics (
  LeagueID                  INT NOT NULL,
  Year                      INT NOT NULL,
  TeamID                    INT NOT NULL,
  Form                      VARCHAR(50),
  WinsHome                  INT,
  WinsAway                  INT,
  DrawsHome                 INT,
  DrawsAway                 INT,
  LossesHome                INT,
  LossesAway                INT,
  GoalsForAverageHome       DECIMAL(5, 2),
  GoalsForAverageAway       DECIMAL(5, 2),
  GoalsAgainstAverageHome   DECIMAL(5, 2),
  GoalsAgainstAverageAway   DECIMAL(5, 2),
  FailedToScoreHome         INT,
  FailedToScoreAway         INT,
  CONSTRAINT PK_TeamStatistics PRIMARY KEY (LeagueID, Year, TeamID),
  CONSTRAINT FK_TeamStatistics_Team FOREIGN KEY (TeamID) REFERENCES Teams(TeamID),
  CONSTRAINT FK_TeamStatistics_Season FOREIGN KEY (LeagueID, Year)
    REFERENCES Seasons(LeagueID, Year)
);

-- API response cache
CREATE TABLE IF NOT EXISTS Cache (
  CacheKey  TEXT PRIMARY KEY,
  Data      TEXT NOT NULL,
  FetchedAt TEXT NOT NULL DEFAULT (datetime('now')),
  ExpiresAt TEXT NOT NULL
);

-- Performance indexes for football and cache data
CREATE INDEX IF NOT EXISTS idx_Fixtures_LeagueID  ON Fixtures(LeagueID);
CREATE INDEX IF NOT EXISTS idx_Fixtures_MatchDate ON Fixtures(MatchDate);
CREATE INDEX IF NOT EXISTS idx_Fixtures_Status    ON Fixtures(Status);
CREATE INDEX IF NOT EXISTS idx_Events_FixtureID   ON Events(FixtureID);
CREATE INDEX IF NOT EXISTS idx_Events_EventType   ON Events(EventType);
CREATE INDEX IF NOT EXISTS idx_FixtureStatistics_TeamID
  ON FixtureStatistics(TeamID);
CREATE INDEX IF NOT EXISTS idx_TeamStatistics_TeamID
  ON TeamStatistics(TeamID);
CREATE INDEX IF NOT EXISTS idx_PlayerTeam_TeamID  ON PlayerTeam(TeamID);
CREATE INDEX IF NOT EXISTS idx_Cache_ExpiresAt    ON Cache(ExpiresAt);
