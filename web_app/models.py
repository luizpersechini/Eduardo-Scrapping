"""
Database models for ANBIMA Scraper Web Application
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ScrapingJob(db.Model):
    """Representa um job de scraping"""
    __tablename__ = 'scraping_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, running, completed, failed
    total_cnpjs = db.Column(db.Integer, default=0)
    successful_cnpjs = db.Column(db.Integer, default=0)
    failed_cnpjs = db.Column(db.Integer, default=0)
    workers = db.Column(db.Integer, default=4)
    use_stealth = db.Column(db.Boolean, default=False)  # Use stealth mode
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    output_file = db.Column(db.String(255), nullable=True)
    pid = db.Column(db.Integer, nullable=True)  # PID of process running the job
    hostname = db.Column(db.String(255), nullable=True)  # Hostname where job runs
    chrome_pids = db.Column(db.Text, nullable=True)  # JSON array of Chrome PIDs
    timeout_seconds = db.Column(db.Integer, default=7200)  # Job timeout (default 2 hours)
    
    # Relationship
    cnpjs = db.relationship('CNPJ', backref='job', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ScrapingJob {self.id} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'status': self.status,
            'total_cnpjs': self.total_cnpjs,
            'successful_cnpjs': self.successful_cnpjs,
            'failed_cnpjs': self.failed_cnpjs,
            'workers': self.workers,
            'use_stealth': self.use_stealth,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'output_file': self.output_file,
            'progress_percentage': round((self.successful_cnpjs + self.failed_cnpjs) / self.total_cnpjs * 100, 1) if self.total_cnpjs > 0 else 0,
            'pid': self.pid,
            'hostname': self.hostname,
            'chrome_pids': self.chrome_pids,
            'timeout_seconds': self.timeout_seconds
        }


class CNPJ(db.Model):
    """Representa um CNPJ individual e seu status de scraping"""
    __tablename__ = 'cnpjs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('scraping_jobs.id'), nullable=False)
    cnpj = db.Column(db.String(20), nullable=False, index=True)
    fund_name = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(50), default='pending')  # pending, processing, success, failed, not_found
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    data_count = db.Column(db.Integer, default=0)  # Número de registros históricos extraídos
    scraped_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<CNPJ {self.cnpj} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'cnpj': self.cnpj,
            'fund_name': self.fund_name,
            'status': self.status,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'data_count': self.data_count,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None
        }


class ScrapedData(db.Model):
    """Armazena os dados extraídos de cada CNPJ"""
    __tablename__ = 'scraped_data'
    
    id = db.Column(db.Integer, primary_key=True)
    cnpj_id = db.Column(db.Integer, db.ForeignKey('cnpjs.id'), nullable=False)
    cnpj = db.Column(db.String(20), nullable=False, index=True)
    fund_name = db.Column(db.String(500), nullable=True)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ScrapedData {self.cnpj} - {self.date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'cnpj': self.cnpj,
            'fund_name': self.fund_name,
            'date': self.date.isoformat(),
            'value': self.value,
            'created_at': self.created_at.isoformat()
        }


