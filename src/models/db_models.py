from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.config.database import Base

class Edificio(Base):
    __tablename__ = "edificios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    direccion = Column(String(150), nullable=True)
    token_url = Column(String(50), unique=True, nullable=False, index=True)
    token_mqtt = Column(String(100), unique=True, nullable=False)

    # Relaciones
    departamentos = relationship("Departamento", back_populates="edificio", cascade="all, delete-orphan")


class Departamento(Base):
    __tablename__ = "departamentos"

    id = Column(Integer, primary_key=True, index=True)
    edificio_id = Column(Integer, ForeignKey("edificios.id", ondelete="CASCADE"), nullable=False)
    nombre_unidad = Column(String(20), nullable=False)

    # Relaciones
    edificio = relationship("Edificio", back_populates="departamentos")
    usuarios = relationship("Usuario", back_populates="departamento")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    departamento_id = Column(Integer, ForeignKey("departamentos.id", ondelete="SET NULL"), nullable=True)
    fcm_token = Column(String(255), nullable=True)
    es_administrador = Column(Boolean, default=False)

    # Relaciones
    departamento = relationship("Departamento", back_populates="usuarios")
