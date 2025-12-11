"""
Configuration management for CIEM Tool
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_default_region: str = Field(default="us-east-1", env="AWS_DEFAULT_REGION")
    aws_regions: List[str] = Field(default=["us-east-1"], env="AWS_REGIONS")
    
    # Database Configuration
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="ciem_db", env="POSTGRES_DB")
    postgres_user: str = Field(default="ciem_user", env="POSTGRES_USER")
    postgres_password: str = Field(default="ciem_password", env="POSTGRES_PASSWORD")
    
    # Neo4j Configuration
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="neo4j_password", env="NEO4J_PASSWORD")
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Backend Configuration
    backend_host: str = Field(default="0.0.0.0", env="BACKEND_HOST")
    backend_port: int = Field(default=8000, env="BACKEND_PORT")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Security
    secret_key: str = Field(default="change-me-in-production", env="SECRET_KEY")
    jwt_secret: str = Field(default="change-me-in-production", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Scanning Configuration
    scan_interval_hours: int = Field(default=24, env="SCAN_INTERVAL_HOURS")
    max_concurrent_regions: int = Field(default=3, env="MAX_CONCURRENT_REGIONS")
    enable_auto_scan: bool = Field(default=False, env="ENABLE_AUTO_SCAN")
    
    # Risk Scoring Thresholds
    risk_critical_threshold: int = Field(default=90, env="RISK_CRITICAL_THRESHOLD")
    risk_high_threshold: int = Field(default=70, env="RISK_HIGH_THRESHOLD")
    risk_medium_threshold: int = Field(default=40, env="RISK_MEDIUM_THRESHOLD")
    
    # Compliance Frameworks
    enable_cis_benchmark: bool = Field(default=True, env="ENABLE_CIS_BENCHMARK")
    enable_nist_framework: bool = Field(default=False, env="ENABLE_NIST_FRAMEWORK")
    enable_iso27001: bool = Field(default=False, env="ENABLE_ISO27001")
    
    # Feature Flags
    enable_cross_account: bool = Field(default=False, env="ENABLE_CROSS_ACCOUNT")
    enable_anomaly_detection: bool = Field(default=False, env="ENABLE_ANOMALY_DETECTION")
    enable_auto_remediation: bool = Field(default=False, env="ENABLE_AUTO_REMEDIATION")
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL database URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
