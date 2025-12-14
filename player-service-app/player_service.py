"""Player Service with CRUD operations using SQLAlchemy ORM."""
from typing import Optional, List
from sqlalchemy import Column, String, Integer, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()


class Player(Base):
    """Player model representing a baseball player."""
    __tablename__ = 'players'

    playerId = Column(String, primary_key=True)
    birthYear = Column(Integer)
    birthMonth = Column(Integer)
    birthDay = Column(Integer)
    birthCountry = Column(String)
    birthState = Column(String)
    birthCity = Column(String)
    nameFirst = Column(String)
    nameLast = Column(String)
    nameGiven = Column(String)
    weight = Column(Integer)
    height = Column(Integer)
    bats = Column(String)
    throws = Column(String)

    def to_dict(self):
        """Convert player to dictionary."""
        return {
            'playerId': self.playerId,
            'birthYear': self.birthYear,
            'birthMonth': self.birthMonth,
            'birthDay': self.birthDay,
            'birthCountry': self.birthCountry,
            'birthState': self.birthState,
            'birthCity': self.birthCity,
            'nameFirst': self.nameFirst,
            'nameLast': self.nameLast,
            'nameGiven': self.nameGiven,
            'weight': self.weight,
            'height': self.height,
            'bats': self.bats,
            'throws': self.throws
        }


class PlayerService:
    """Service class for Player CRUD operations."""

    def __init__(self, db_url='sqlite:///player.db'):
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def close(self):
        """Close the session."""
        self.session.close()

    # CREATE
    def create_player(self, player_data: dict) -> Player:
        """Create a new player."""
        player = Player(**player_data)
        self.session.add(player)
        self.session.commit()
        self.session.refresh(player)
        return player

    # READ
    def get_player(self, player_id: str) -> Optional[Player]:
        """Get a player by ID."""
        return self.session.query(Player).filter(Player.playerId == player_id).first()

    def get_all_players(self, limit: int = 100, offset: int = 0) -> List[Player]:
        """Get all players with pagination."""
        return self.session.query(Player).offset(offset).limit(limit).all()

    # UPDATE
    def update_player(self, player_id: str, player_data: dict) -> Optional[Player]:
        """Update an existing player."""
        player = self.get_player(player_id)
        if not player:
            return None
        for key, value in player_data.items():
            if hasattr(player, key) and key != 'playerId':
                setattr(player, key, value)
        self.session.commit()
        self.session.refresh(player)
        return player

    # DELETE
    def delete_player(self, player_id: str) -> bool:
        """Delete a player by ID."""
        player = self.get_player(player_id)
        if not player:
            return False
        self.session.delete(player)
        self.session.commit()
        return True

    # QUERIES
    def search_by_country(self, country: str) -> List[Player]:
        """Find players by birth country."""
        return self.session.query(Player).filter(Player.birthCountry == country).all()

    def search_by_name(self, name: str) -> List[Player]:
        """Find players by first or last name (case-insensitive)."""
        search = f"%{name}%"
        return self.session.query(Player).filter(
            (Player.nameFirst.ilike(search)) | (Player.nameLast.ilike(search))
        ).all()

    def search_by_birth_year(self, year: int) -> List[Player]:
        """Find players born in a specific year."""
        return self.session.query(Player).filter(Player.birthYear == year).all()

    def search_by_birth_year_range(self, start_year: int, end_year: int) -> List[Player]:
        """Find players born between two years."""
        return self.session.query(Player).filter(
            Player.birthYear >= start_year,
            Player.birthYear <= end_year
        ).all()

    def count_players(self) -> int:
        """Get total count of players."""
        return self.session.query(Player).count()

    def count_players_by_country(self) -> List[tuple]:
        """Get player count grouped by country."""
        return self.session.query(
            Player.birthCountry,
            func.count(Player.playerId)
        ).group_by(Player.birthCountry).all()
