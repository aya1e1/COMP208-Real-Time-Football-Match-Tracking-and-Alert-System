
CREATE TABLE Teams (
  TeamID INT,
  Name VARCHAR(20),
  Abbreviation VARCHAR(5),
  City VARCHAR(20),
  LeagueID INT,
  CONSTRAINT PK_Teams PRIMARY KEY (TeamID)
  CONSTRAINT FK_Teams_Leagues FOREIGN KEY (LeagueID) REFERENCES Leagues(LeagueID)
);

CREATE TABLE League (
  LeagueID INT,
  Name VARCHAR(20),
  CONSTRAINT PK_Leagues PRIMARY KEY (LeagueID)
);

CREATE TABLE LeagueTable (
  LeagueID INT,
  TeamID INT,
  Position INT, 
  Points INT,
  Played INT,
  GF INT,
  GA INT,
  CONSTRAINT FK_LeagueTable_Teams FOREIGN KEY (TeamID) REFERENCES Teams(TeamID), 
  CONSTRAINT FK_LeagueTable_League FOREIGN KEY (LeagueID) REFERENCES League(LeagueID)
);

CREATE TABLE Seasons (
  SeasonID INT PRIMARY KEY,
  LeagueID INT,
  Name VARCHAR(50),
  StartDate DATE,
  EndDate DATE,
  CONSTRAINT PK_Seasons PRIMARY KEY (SeasonID),
  CONSTRAINT FK_Seasons_Leagues FOREIGN KEY (LeagueID) REFERENCES Leagues(LeagueID)
);


CREATE TABLE Player (
  PlayerID INT,
  Name VARCHAR(20),
  MainPosition VARCHAR(20),
  DateOfBirth DATE,
  Nationality VARCHAR(20),
  CONSTRAINT PK_Player PRIMARY KEY (PlayerID)
);

CREATE TABLE PlayerTeam{
  PlayerID INT,
  TeamID INT,
  Shirt_Number INT,
  Contract_Type VARCHAR(220),
  CONSTRAINT FK_PlayerTeam_Player FOREIGN KEY (PlayerID) REFERENCES Player(PlayerID)
  
}

CREATE TABLE Fixtures{
  FixtureID INT,
  LeagueID INT,
  Hometeam INT,
  AawayTeam INT,
  Location VARCHAR(20),
  MatchDate DATETIME,
  Completed BOOLEAN DEFAULT FALSE
  HomeScore INT DEFAULT 0,
  AwayScore INT DEFAULT 0,
  CONSTRAINT PK_Fixtures PRIMARY KEY (FixtureID),
  CONSTRAINT FK_Fixtures_Leagues FOREIGN KEY (LeagueID) REFERENCES Leagues(LeagueID),
  CONSTRAINT FK_Fixtures_HomeTeam FOREIGN KEY (HomeTeam) REFERENCES Teams(TeamID),
  CONSTRAINT FK_Fixtures_AwayTeam FOREIGN KEY (AwayTeam) REFERENCES Teams(TeamID),
  CONSTRAINT CHK_Fixtures_Score CHECK (HomeScore >= 0 AND AwayScore >= 0),
  CONSTRAINT CHK_Fixtures_DifferentTeams CHECK (HomeTeam <> AwayTeam)
}

CREATE TABLE Events {
  FixtureID INT,
  EventID INT, 
  PlayerID INT,
  TeamID INT,
  EventType INT,
  Description VARCHAR(20),
  Timestamp DATE,
  CONSTRAINT Pk_Events PRIMARY KEY (FixtureID, EventID)
  CONSTRAINT FK_Events_Player FOREIGN KEY (PlayerID) REFERENCES Player(PlayerID),
  CONSTRAINT FK_Events_Fixture FOREIGN KEY (FixtureID) REFERENCES Fixtures(FixtureID)
}