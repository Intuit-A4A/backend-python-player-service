"""Player Service with CRUD operations using SQLAlchemy ORM."""
from typing import Optional, List
from sqlalchemy import Column, String, Integer, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Player(Base):
    """Player model."""
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
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class PlayerService:
    """Service class for Player CRUD operations."""

    def __init__(self, db_url='sqlite:///player.db', create_tables=False):
        self.engine = create_engine(db_url, echo=False)
        if create_tables:
            Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def close(self):
        self.session.close()

    # CREATE
    def create_player(self, data: dict) -> Player:
        player = Player(**data)
        self.session.add(player)
        self.session.commit()
        self.session.refresh(player)
        return player

    # READ
    def get_player(self, player_id: str) -> Optional[Player]:
        return self.session.query(Player).filter(Player.playerId == player_id).first()

    def get_all_players(self, limit: int = 100, offset: int = 0) -> List[Player]:
        return self.session.query(Player).offset(offset).limit(limit).all()

    # UPDATE
    def update_player(self, player_id: str, data: dict) -> Optional[Player]:
        player = self.get_player(player_id)
        if not player:
            return None
        for key, value in data.items():
            if hasattr(player, key) and key != 'playerId':
                setattr(player, key, value)
        self.session.commit()
        self.session.refresh(player)
        return player

    # DELETE
    def delete_player(self, player_id: str) -> bool:
        player = self.get_player(player_id)
        if not player:
            return False
        self.session.delete(player)
        self.session.commit()
        return True

    # QUERIES
    def search_by_country(self, country: str) -> List[Player]:
        return self.session.query(Player).filter(Player.birthCountry == country).all()

    def search_by_name(self, name: str) -> List[Player]:
        search = f"%{name}%"
        return self.session.query(Player).filter(
            (Player.nameFirst.ilike(search)) | (Player.nameLast.ilike(search))
        ).all()

    def search_by_birth_year(self, year: int) -> List[Player]:
        return self.session.query(Player).filter(Player.birthYear == year).all()

    def search_by_birth_year_range(self, start: int, end: int) -> List[Player]:
        return self.session.query(Player).filter(
            Player.birthYear >= start, Player.birthYear <= end
        ).all()

    def count_players(self) -> int:
        return self.session.query(Player).count()

    def count_by_country(self) -> List[tuple]:
        return self.session.query(
            Player.birthCountry, func.count(Player.playerId)
        ).group_by(Player.birthCountry).all()
