CREATE TABLE Users (
    UserId int PRIMARY KEY IDENTITY(1,1),
    FirstName varchar(900) NOT NULL,
    LastName varchar(900) NOT NULL,
    Email varchar(900) UNIQUE NOT NULL,
    APIKey varchar(900) UNIQUE NOT NULL);

CREATE TABLE Movies (
	MovieId int PRIMARY KEY IDENTITY(1,1),
	UserId int FOREIGN KEY REFERENCES Users(UserId) NOT NULL,
	Name varchar(900) NOT NULL,
	UploadDate smalldatetime NOT NULL,
	UploadStatus BIT,
	CONSTRAINT Unique_Movie UNIQUE (UserId,Name));

CREATE UNIQUE INDEX movie_name_ind
ON Movies(UserId,Name);

CREATE TABLE Frames (
	FrameId int PRIMARY KEY IDENTITY(1,1),
	MovieId int FOREIGN KEY REFERENCES Movies(MovieId) NOT NULL,
	FrameNumber varchar(900) NOT NULL,
	CONSTRAINT Unique_Frame UNIQUE (MovieId,FrameNumber));

CREATE UNIQUE INDEX frame_ind
ON Frames(MovieId,FrameNumber);

CREATE TABLE Searches (
    SearchId int PRIMARY KEY IDENTITY(1,1),
    MovieId int FOREIGN KEY REFERENCES Movies(MovieId) NOT NULL,
    SearchWord varchar(900) NOT NULL,
    SearchDate smalldatetime NOT NULL,
    SearchStatus BIT,
    CONSTRAINT Unique_Search UNIQUE (MovieId,SearchWord));

CREATE UNIQUE INDEX search_ind
ON Searches(MovieId,SearchWord);

CREATE TABLE Results (
    ResultId int PRIMARY KEY IDENTITY(1,1),
    SearchId int FOREIGN KEY REFERENCES Searches(SearchId) NOT NULL,
    URL varchar(900) NOT NULL,
    CONSTRAINT Unique_Result UNIQUE (SearchId,URL));

CREATE UNIQUE INDEX result_ind
ON Results(SearchId,URL);