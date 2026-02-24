-- Teams
CREATE TABLE Teams (
  TeamID INT,
  Name VARCHAR(50) NOT NULL,
  Abbreviation VARCHAR(10),
  City VARCHAR(50),
  LeagueID INT,
  CONSTRAINT PK_Teams PRIMARY KEY (TeamID),
  CONSTRAINT FK_Teams_Leagues FOREIGN KEY (LeagueID) REFERENCES Leagues(LeagueID),
);

-- League
CREATE TABLE League (
  LeagueID INT,
  Name VARCHAR(50) NOT NULL,
  CONSTRAINT PK_Leagues PRIMARY KEY (LeagueID),
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
  CONSTRAINT FK_LeagueTable_Teams FOREIGN KEY (TeamID) REFERENCES Teams(TeamID), 
  CONSTRAINT FK_LeagueTable_League FOREIGN KEY (LeagueID) REFERENCES League(LeagueID),
);

-- Seasons
CREATE TABLE Seasons (
  SeasonID INT PRIMARY KEY,
  LeagueID INT not null,
  Name VARCHAR(50),
  StartDate DATE,
  EndDate DATE,
  CONSTRAINT PK_Seasons PRIMARY KEY (SeasonID),
  CONSTRAINT FK_Seasons_Leagues FOREIGN KEY (LeagueID) REFERENCES Leagues(LeagueID),
);

-- Players
CREATE TABLE Player (
  PlayerID INT,
  Name VARCHAR(100) NOT NULL,
  MainPosition VARCHAR(50),
  DateOfBirth DATE,
  Nationality VARCHAR(50),
  CONSTRAINT PK_Player PRIMARY KEY (PlayerID),
);

-- PlayerTeam
CREATE TABLE PlayerTeam{
  PlayerID INT NOT NULL,
  TeamID INT NOT NULL,
  Shirt_Number INT,
  Contract_Type VARCHAR(220),
  CONSTRAINT FK_PlayerTeam_Player FOREIGN KEY (PlayerID) REFERENCES Player(PlayerID),
  
}

-- Fixtures
CREATE TABLE Fixtures{
  FixtureID INT,
  LeagueID INT NOT NULL,
  Hometeam INT NOT NULL,
  AawayTeam INT NOT NULL,
  Location VARCHAR(100),
  MatchDate DATETIME NOT NULL,
  Completed BOOLEAN DEFAULT FALSE,
  HomeScore INT DEFAULT 0,
  AwayScore INT DEFAULT 0,
  CONSTRAINT PK_Fixtures PRIMARY KEY (FixtureID),
  CONSTRAINT FK_Fixtures_Leagues FOREIGN KEY (LeagueID) REFERENCES Leagues(LeagueID),
  CONSTRAINT FK_Fixtures_HomeTeam FOREIGN KEY (HomeTeam) REFERENCES Teams(TeamID),
  CONSTRAINT FK_Fixtures_AwayTeam FOREIGN KEY (AwayTeam) REFERENCES Teams(TeamID),
  CONSTRAINT CHK_Fixtures_Score CHECK (HomeScore >= 0 AND AwayScore >= 0),
  CONSTRAINT CHK_Fixtures_DifferentTeams CHECK (HomeTeam <> AwayTeam)
}

-- Events
CREATE TABLE Events {
  FixtureID INT NOT NULL,
  EventID INT NOT NULL, 
  PlayerID INT,
  TeamID INT NOT NULL,
  EventType INT,
  Description VARCHAR(255),
  Timestamp DATE,
  CONSTRAINT Pk_Events PRIMARY KEY (FixtureID, EventID),
  CONSTRAINT FK_Events_Player FOREIGN KEY (PlayerID) REFERENCES Player(PlayerID),
  CONSTRAINT FK_Events_Fixture FOREIGN KEY (FixtureID) REFERENCES Fixtures(FixtureID),
}
